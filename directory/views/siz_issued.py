# 📁 directory/views/siz_issued.py
from django.views.generic import CreateView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO

from django.contrib.staticfiles import finders
import os

from directory.models import Employee, SIZ, SIZNorm, SIZIssued, Position
from directory.forms.siz_issued import SIZIssueForm, SIZIssueMassForm, SIZIssueReturnForm


class SIZIssueFormView(LoginRequiredMixin, CreateView):
    """
    📝 Представление для выдачи СИЗ сотруднику
    """
    model = SIZIssued
    form_class = SIZIssueForm
    template_name = 'directory/siz_issued/issue_form.html'

    def get_success_url(self):
        """
        🔗 Возвращает URL для перенаправления после успешной выдачи СИЗ
        """
        return reverse('directory:siz:siz_personal_card', kwargs={'employee_id': self.object.employee.id})

    def get_form_kwargs(self):
        """
        📋 Передаем дополнительные параметры в форму
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        # Если в URL есть параметр employee_id, передаем его в форму
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            kwargs['employee_id'] = employee_id

        return kwargs

    def get_context_data(self, **kwargs):
        """
        📊 Добавляем дополнительные данные в контекст
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Выдача СИЗ'

        # Если есть employee_id в URL, добавляем информацию о сотруднике
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            employee = get_object_or_404(Employee, id=employee_id)
            context['employee'] = employee

            # Получаем нормы СИЗ для должности сотрудника
            if employee.position:
                norms = SIZNorm.objects.filter(
                    position=employee.position
                ).select_related('siz')

                # Группируем нормы по условиям
                context['base_norms'] = norms.filter(condition='')

                condition_groups = {}
                for norm in norms.exclude(condition=''):
                    if norm.condition not in condition_groups:
                        condition_groups[norm.condition] = []
                    condition_groups[norm.condition].append(norm)

                context['condition_groups'] = [
                    {'name': condition, 'norms': norms}
                    for condition, norms in condition_groups.items()
                ]

        return context

    def form_valid(self, form):
        """
        ✅ Обработка валидной формы
        """
        # Сохраняем объект
        response = super().form_valid(form)

        # Добавляем сообщение об успешной выдаче
        messages.success(
            self.request,
            f"✅ СИЗ '{self.object.siz.name}' успешно выдано сотруднику {self.object.employee.full_name_nominative}"
        )

        return response


class SIZPersonalCardView(LoginRequiredMixin, DetailView):
    """
    👤 Представление для отображения личной карточки учета СИЗ сотрудника
    """
    model = Employee
    template_name = 'directory/siz_issued/personal_card.html'
    context_object_name = 'employee'

    def get_object(self):
        """
        🔍 Получаем объект сотрудника по его ID
        """
        return get_object_or_404(Employee, id=self.kwargs.get('employee_id'))

    def get_context_data(self, **kwargs):
        """
        📊 Добавляем дополнительные данные в контекст

        Улучшенная логика:
        1. Получаем как прямые нормы должности, так и эталонные
        2. Объединяем их, отдавая приоритет прямым нормам
        3. Группируем по условиям применения
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f'Личная карточка учета СИЗ - {self.object.full_name_nominative}'

        # Получаем все выданные сотруднику СИЗ
        issued_items = SIZIssued.objects.filter(
            employee=self.object
        ).select_related('siz').order_by('-issue_date')

        context['issued_items'] = issued_items

        # Получаем нормы СИЗ для должности сотрудника
        if self.object.position:
            # 🆕 Улучшенная логика получения норм: объединяем конкретные и эталонные
            position = self.object.position

            # 1. Получаем непосредственные нормы должности
            direct_norms = SIZNorm.objects.filter(
                position=position
            ).select_related('siz')

            # 2. Получаем эталонные нормы по названию должности
            reference_norms = Position.find_reference_norms(position.position_name)

            # 3. Формируем словарь норм, где ключ - комбинация siz_id + condition
            norm_dict = {}

            # Сначала добавляем эталонные нормы (они будут перезаписаны прямыми при совпадении)
            for norm in reference_norms:
                key = f"{norm.siz_id}_{norm.condition}"
                norm_dict[key] = norm

            # Затем добавляем прямые нормы с более высоким приоритетом
            for norm in direct_norms:
                key = f"{norm.siz_id}_{norm.condition}"
                norm_dict[key] = norm

            # 4. Группируем нормы по условиям
            base_norms = []
            condition_groups = {}

            for key, norm in norm_dict.items():
                if not norm.condition:
                    base_norms.append(norm)
                else:
                    if norm.condition not in condition_groups:
                        condition_groups[norm.condition] = []
                    condition_groups[norm.condition].append(norm)

            # 5. Сортируем нормы по порядку (order) и названию СИЗ
            base_norms.sort(key=lambda x: (x.order, x.siz.name))

            context['base_norms'] = base_norms
            context['condition_groups'] = [
                {'name': condition, 'norms': sorted(norms, key=lambda x: (x.order, x.siz.name))}
                for condition, norms in condition_groups.items()
            ]

        return context


class SIZIssueReturnView(LoginRequiredMixin, UpdateView):
    """
    🔄 Представление для возврата выданного СИЗ
    """
    model = SIZIssued
    form_class = SIZIssueReturnForm
    template_name = 'directory/siz_issued/return_form.html'
    pk_url_kwarg = 'siz_issued_id'

    def get_success_url(self):
        """
        🔗 Возвращает URL для перенаправления после успешного возврата СИЗ
        """
        return reverse('directory:siz:siz_personal_card', kwargs={'employee_id': self.object.employee.id})

    def get_context_data(self, **kwargs):
        """
        📊 Добавляем дополнительные данные в контекст
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Возврат СИЗ'
        context['employee'] = self.object.employee
        context['siz_name'] = self.object.siz.name
        context['issue_date'] = self.object.issue_date

        return context

    def form_valid(self, form):
        """
        ✅ Обработка валидной формы
        """
        # Сохраняем объект
        response = super().form_valid(form)

        # Добавляем сообщение об успешном возврате
        messages.success(
            self.request,
            f"✅ СИЗ '{self.object.siz.name}' успешно возвращено"
        )

        return response


@login_required
@require_GET
def employee_siz_issued_list(request, employee_id):
    """
    📋 Получение списка выданных СИЗ для конкретного сотрудника

    Используется для API и формирования оборотной стороны личной карточки.

    Args:
        request: HttpRequest объект
        employee_id: ID сотрудника

    Returns:
        JsonResponse с данными о выданных СИЗ
    """
    employee = get_object_or_404(Employee, pk=employee_id)

    # Получаем все СИЗ, выданные сотруднику
    issued_items = SIZIssued.objects.filter(
        employee=employee
    ).select_related('siz').order_by('-issue_date')

    # Формируем данные для JSON
    result = {
        'employee_id': employee.id,
        'employee_name': employee.full_name_nominative,
        'position': employee.position.position_name if employee.position else "",
        'organization': employee.organization.short_name_ru,
        'issued_items': []
    }

    # Добавляем информацию о каждом выданном СИЗ
    for item in issued_items:
        item_data = {
            'id': item.id,
            'siz_name': item.siz.name,
            'siz_classification': item.siz.classification,
            'issue_date': item.issue_date.strftime('%d.%m.%Y'),
            'quantity': item.quantity,
            'wear_percentage': item.wear_percentage,
            'is_returned': item.is_returned,
            'return_date': item.return_date.strftime('%d.%m.%Y') if item.return_date else None,
            'notes': item.notes,
            'condition': item.condition
        }
        result['issued_items'].append(item_data)

    return JsonResponse(result)


@login_required
@require_GET
def position_siz_norms(request, position_id):
    """
    📋 API для получения норм СИЗ по должности

    Args:
        request: HttpRequest объект
        position_id: ID должности

    Returns:
        JsonResponse с данными о нормах СИЗ
    """
    position = get_object_or_404(Position, pk=position_id)

    # Получаем нормы СИЗ для должности
    norms = SIZNorm.objects.filter(
        position=position
    ).select_related('siz')

    # Формируем данные для JSON
    result = {
        'position_id': position.id,
        'position_name': position.position_name,
        'norms': []
    }

    # Добавляем информацию о каждой норме СИЗ
    for norm in norms:
        norm_data = {
            'id': norm.id,
            'siz_id': norm.siz.id,
            'siz_name': norm.siz.name,
            'classification': norm.siz.classification,
            'quantity': norm.quantity,
            'condition': norm.condition,
            'unit': norm.siz.unit,
            'wear_period': norm.siz.wear_period
        }
        result['norms'].append(norm_data)

    return JsonResponse(result)


@login_required
def export_personal_card_pdf(request, employee_id):
    """
    📄 Экспорт личной карточки учета СИЗ в формате PDF для печати на A4
    Использует xhtml2pdf вместо WeasyPrint для большей совместимости с Windows

    Args:
        request: HttpRequest объект
        employee_id: ID сотрудника

    Returns:
        HttpResponse с PDF-документом
    """
    # Получаем объект сотрудника
    employee = get_object_or_404(Employee, id=employee_id)

    # Получаем данные для карточки (аналогично методу get_context_data в SIZPersonalCardView)
    # 📊 Данные о выданных СИЗ
    issued_items = SIZIssued.objects.filter(
        employee=employee
    ).select_related('siz').order_by('-issue_date')

    # 📊 Данные о нормах СИЗ
    base_norms = []
    condition_groups = []

    if employee.position:
        # 🆕 Логика получения норм (аналогично SIZPersonalCardView)
        position = employee.position

        # Получаем непосредственные нормы должности
        direct_norms = SIZNorm.objects.filter(
            position=position
        ).select_related('siz')

        # Получаем эталонные нормы по названию должности
        reference_norms = Position.find_reference_norms(position.position_name)

        # Формируем словарь норм, где ключ - комбинация siz_id + condition
        norm_dict = {}

        # Добавляем эталонные нормы
        for norm in reference_norms:
            key = f"{norm.siz_id}_{norm.condition}"
            norm_dict[key] = norm

        # Добавляем прямые нормы с более высоким приоритетом
        for norm in direct_norms:
            key = f"{norm.siz_id}_{norm.condition}"
            norm_dict[key] = norm

        # Группируем нормы по условиям
        condition_groups_dict = {}

        for key, norm in norm_dict.items():
            if not norm.condition:
                base_norms.append(norm)
            else:
                if norm.condition not in condition_groups_dict:
                    condition_groups_dict[norm.condition] = []
                condition_groups_dict[norm.condition].append(norm)

        # Сортируем нормы
        base_norms.sort(key=lambda x: (x.order, x.siz.name))

        condition_groups = [
            {'name': condition, 'norms': sorted(norms, key=lambda x: (x.order, x.siz.name))}
            for condition, norms in condition_groups_dict.items()
        ]

    # Подготавливаем контекст для шаблона
    context = {
        'employee': employee,
        'issued_items': issued_items,
        'base_norms': base_norms,
        'condition_groups': condition_groups,
        'title': f'Личная карточка учета СИЗ - {employee.full_name_nominative}',
        'is_pdf': True,  # Флаг для шаблона, что это PDF-версия
        'now': timezone.now(),  # Текущая дата и время для отображения в PDF
    }

    # Загружаем шаблон
    template = get_template('directory/siz_issued/personal_card_pdf.html')
    html_content = template.render(context)

    # Создаем буфер для PDF
    result = BytesIO()

    # Создаем PDF с использованием xhtml2pdf
    pdf = pisa.pisaDocument(
        BytesIO(html_content.encode("UTF-8")),
        result,
        encoding='UTF-8'
    )

    # Проверяем наличие ошибок
    if not pdf.err:
        # Формируем HTTP-ответ с PDF
        response = HttpResponse(result.getvalue(), content_type='application/pdf')

        # Формируем имя файла для скачивания
        # Транслитерация имени для корректного отображения в заголовке Content-Disposition
        employee_name = employee.full_name_nominative.replace(' ', '_')
        filename = f"siz_card_{employee.id}_{employee_name}.pdf"

        # Устанавливаем заголовок для скачивания файла
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    # В случае ошибки возвращаем сообщение об ошибке
    return HttpResponse("Ошибка создания PDF", status=500)