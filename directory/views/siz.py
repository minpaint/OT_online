from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Subquery, OuterRef, IntegerField
from django.db.models.functions import Coalesce
from directory.models import Employee, SIZIssued
from directory.models.siz import SIZ, SIZNorm
from directory.models.position import Position
from directory.models.subdivision import StructuralSubdivision
from directory.forms.siz import SIZForm, SIZNormForm
from directory.mixins import AccessControlMixin, AccessControlObjectMixin
from directory.utils.permissions import AccessControlHelper
import zipfile
import io
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SIZListView(LoginRequiredMixin, ListView):
    """
    🛡️ Показ списка СИЗ
    """
    model = SIZ
    template_name = 'directory/siz/list.html'
    context_object_name = 'siz_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Средства индивидуальной защиты'

        # Получаем доступные организации через AccessControlHelper
        accessible_orgs = AccessControlHelper.get_accessible_organizations(
            self.request.user, self.request
        )

        # Фильтрация списка сотрудников по доступным организациям
        employees = Employee.objects.filter(organization__in=accessible_orgs)
        context['employees'] = employees.order_by('full_name_nominative')

        # Фильтрация последних выданных СИЗ по доступным организациям
        recent_issued = SIZIssued.objects.filter(
            employee__organization__in=accessible_orgs
        ).select_related('employee', 'siz')
        context['recent_issued'] = recent_issued.order_by('-issue_date')[:10]

        return context


class SIZNormCreateView(LoginRequiredMixin, CreateView):
    """
    📝 Создание нормы выдачи СИЗ
    """
    model = SIZNorm
    form_class = SIZNormForm
    template_name = 'directory/siz/norm_form.html'
    success_url = reverse_lazy('directory:siz:siz_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        position_id = self.request.GET.get('position_id')
        if position_id:
            kwargs['position_id'] = position_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание нормы выдачи СИЗ'

        position_id = self.request.GET.get('position_id')
        if position_id:
            position = Position.objects.filter(id=position_id).first()
            if position:
                context['position'] = position

        return context


def position_siz_norms(request, position_id):
    """
    📋 Представление для отображения норм СИЗ для должности
    """
    position = get_object_or_404(Position, pk=position_id)

    # Получаем все нормы СИЗ для данной должности
    base_norms = SIZNorm.objects.filter(position=position, condition='').select_related('siz')

    # Получаем уникальные условия (кроме пустых)
    conditions = SIZNorm.objects.filter(position=position).exclude(condition='').values_list('condition',
                                                                                             flat=True).distinct()

    # Формируем группы СИЗ по условиям
    groups = []
    for condition in conditions:
        norms = SIZNorm.objects.filter(position=position, condition=condition).select_related('siz').order_by('order')
        groups.append({
            'name': condition,
            'norms': norms
        })

    context = {
        'position': position,
        'base_norms': base_norms,
        'groups': groups
    }

    return render(request, 'admin/directory/position/siz_norms.html', context)


def siz_by_position_api(request):
    """
    🔍 API для получения норм СИЗ для должности по AJAX-запросу
    """
    position_id = request.GET.get('position_id')
    if not position_id:
        return JsonResponse({'error': 'Не указан ID должности'}, status=400)

    try:
        position = Position.objects.get(pk=position_id)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена'}, status=404)

    norms = SIZNorm.objects.filter(position=position).select_related('siz')

    # Формируем результат
    result = {
        'position_id': position.id,
        'position_name': position.position_name,
        'norms': []
    }

    for norm in norms:
        result['norms'].append({
            'id': norm.id,
            'siz_id': norm.siz.id,
            'siz_name': norm.siz.name,
            'classification': norm.siz.classification,
            'quantity': norm.quantity,
            'condition': norm.condition,
            'wear_period': norm.siz.wear_period,
            'unit': norm.siz.unit
        })

    return JsonResponse(result)


@require_GET
def get_position_siz_norms(request, position_id):
    """
    API для получения норм СИЗ для должности
    Используется для формирования лицевой стороны личной карточки
    """
    position = get_object_or_404(Position, pk=position_id)

    # Получаем все нормы СИЗ для данной должности
    norms = position.siz_norms.all().select_related('siz')

    # Формируем результат
    result = {
        'position_name': position.position_name,
        'base_norms': [],
        'conditional_norms': []
    }

    # Разделяем на основные и условные нормы
    for norm in norms:
        norm_data = {
            'siz_name': norm.siz.name,
            'classification': norm.siz.classification,
            'unit': norm.siz.unit,
            'quantity': norm.quantity,
            'wear_period': "До износа" if norm.siz.wear_period == 0 else f"{norm.siz.wear_period} мес."
        }

        if norm.condition:
            # Если есть условие - добавляем в условные нормы
            result['conditional_norms'].append({
                'condition': norm.condition,
                'norm': norm_data
            })
        else:
            # Иначе - в основные
            result['base_norms'].append(norm_data)

    return JsonResponse(result)


@require_GET
def get_employee_issued_siz(request, employee_id):
    """
    API для получения фактически выданных СИЗ сотруднику
    Используется для формирования оборотной стороны личной карточки
    """
    employee = get_object_or_404(Employee, pk=employee_id)

    # Здесь должен быть код для получения выданных СИЗ
    # Пока это заглушка, т.к. у нас нет соответствующей модели

    # TODO: Заменить на получение реальных данных, когда будет модель выдачи СИЗ
    issued_siz = []

    return JsonResponse({
        'employee_name': f"{employee.last_name} {employee.first_name}",
        'position': employee.position.position_name if employee.position else "",
        'issued_siz': issued_siz
    })


@require_GET
def get_siz_details(request, siz_id):
    """
    🔍 API для получения детальной информации о СИЗ
    Используется для автозаполнения полей в форме редактирования норм
    """
    siz = get_object_or_404(SIZ, pk=siz_id)

    # Формируем данные о СИЗ для отображения в форме
    result = {
        'id': siz.id,
        'name': siz.name,
        'classification': siz.classification,
        'unit': siz.unit,
        'wear_period': siz.wear_period,
        'wear_period_display': "До износа" if siz.wear_period == 0 else f"{siz.wear_period} мес."
    }

    return JsonResponse(result)


# =============================================
# МАССОВАЯ ГЕНЕРАЦИЯ КАРТОЧЕК СИЗ
# =============================================


class SIZMassGenerationView(LoginRequiredMixin, ListView):
    """
    📦 Массовая генерация карточек СИЗ по структурным подразделениям
    """
    model = StructuralSubdivision
    template_name = 'directory/siz/mass_generation.html'
    context_object_name = 'subdivisions'

    def get_queryset(self):
        """Получаем только те подразделения, где есть сотрудники с нормами СИЗ"""
        accessible_orgs = AccessControlHelper.get_accessible_organizations(
            self.request.user, self.request
        )

        # Subquery to get the count of employees with SIZ norms for each subdivision.
        # We define a subquery that looks at the Employee model.
        employees_with_norms = Employee.objects.filter(
            # Then we apply the filter conditions to find employees with SIZ norms.
            Q(position__siz_norms__isnull=False) |
            Q(position__position_name__in=Position.objects.filter(
                siz_norms__isnull=False
            ).values_list('position_name', flat=True)),
            # We link each employee to the outer StructuralSubdivision query via their position path.
            position__department__subdivision=OuterRef('pk')
        ).order_by().values(
            # We need to tell the subquery to group by the subdivision to count per subdivision.
            'position__department__subdivision'
        ).annotate(
            # We count the unique employees.
            count=Count('id', distinct=True)
        ).values('count')

        queryset = StructuralSubdivision.objects.filter(
            organization__in=accessible_orgs
        ).annotate(
            # Annotate the main queryset with the count from the subquery.
            # Use Coalesce to handle cases where a subdivision has no such employees (results in NULL).
            employees_with_norms_count=Coalesce(
                Subquery(employees_with_norms, output_field=IntegerField()),
                0
            )
        ).filter(
            # Now filter the main queryset to only include subdivisions with more than 0 such employees.
            employees_with_norms_count__gt=0
        ).select_related('organization').order_by('organization__full_name_ru', 'name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Массовая генерация карточек СИЗ'
        return context


@login_required
@require_POST
def generate_siz_cards_bulk(request):
    """
    📦 Генерация ZIP-архива с карточками СИЗ для выбранных подразделений
    """
    from directory.document_generators.siz_card_docx_generator import generate_siz_card_docx

    subdivision_ids = request.POST.getlist('subdivision_ids')

    if not subdivision_ids:
        return HttpResponse("Не выбрано ни одного подразделения", status=400)

    # Создаём ZIP-архив в памяти
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        generated_count = 0
        errors = []

        for subdivision_id in subdivision_ids:
            try:
                subdivision = StructuralSubdivision.objects.get(pk=subdivision_id)

                # Получаем всех сотрудников подразделения, у которых есть нормы СИЗ
                employees = Employee.objects.filter(
                    position__department__subdivision=subdivision
                ).select_related('position', 'position__department')

                for employee in employees:
                    if not employee.position:
                        continue

                    # Проверяем, есть ли нормы для должности (прямо или через эталонную)
                    has_norms = SIZNorm.objects.filter(position=employee.position).exists()

                    if not has_norms:
                        # Ищем эталонную должность
                        reference_positions = Position.objects.filter(
                            position_name=employee.position.position_name
                        )
                        has_norms = any(
                            SIZNorm.objects.filter(position=pos).exists()
                            for pos in reference_positions
                        )

                    if not has_norms:
                        continue

                    # Генерируем карточку
                    result = generate_siz_card_docx(employee, request.user)

                    if result and 'content' in result:
                        # Формируем безопасное имя файла
                        safe_subdivision = re.sub(r'[<>:"/\\|?*]', '_', subdivision.name)
                        safe_employee = re.sub(r'[<>:"/\\|?*]', '_', employee.full_name_nominative)

                        # Добавляем файл в архив
                        file_path = f"{safe_subdivision}/{safe_employee}_карточка_СИЗ.docx"
                        zip_file.writestr(file_path, result['content'])
                        generated_count += 1

                        logger.info(f"Добавлена карточка: {file_path}")
                    else:
                        errors.append(f"Ошибка генерации для {employee.full_name_nominative}")

            except Exception as e:
                logger.error(f"Ошибка при обработке подразделения {subdivision_id}: {e}")
                errors.append(f"Ошибка подразделения ID={subdivision_id}: {str(e)}")

        # Добавляем файл со сводкой
        summary = f"""Массовая генерация карточек СИЗ
Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Сгенерировано карточек: {generated_count}

"""
        if errors:
            summary += "Ошибки:\n" + "\n".join(errors)

        zip_file.writestr("_summary.txt", summary.encode('utf-8'))

    # Отправляем архив пользователю
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Карточки_СИЗ_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'

    logger.info(f"Массовая генерация завершена. Создано файлов: {generated_count}")

    return response