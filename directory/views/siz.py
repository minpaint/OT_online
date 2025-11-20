from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from directory.models import Employee, SIZIssued  # Добавляем импорт SIZIssued

from directory.models.siz import SIZ, SIZNorm
from directory.models.position import Position
from directory.models import Employee
from directory.forms.siz import SIZForm, SIZNormForm
from directory.mixins import AccessControlMixin, AccessControlObjectMixin
from directory.utils.permissions import AccessControlHelper


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