from django.views.generic import FormView, DetailView, UpdateView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F, Sum, Case, When, Value, IntegerField
from django.views.decorators.http import require_GET

from directory.models.siz import SIZ, SIZNorm
from directory.models.siz_issued import SIZIssued
from directory.models.employee import Employee
from directory.models.position import Position
from directory.forms.siz_issued import SIZIssueMassForm, SIZIssueReturnForm


class SIZIssueFormView(LoginRequiredMixin, FormView):
    """
    📝 Представление для формы выдачи СИЗ сотруднику
    """
    template_name = 'directory/siz_issued/issue_form.html'
    form_class = SIZIssueMassForm
    success_url = reverse_lazy('directory:siz:siz_list')

    def get_form_kwargs(self):
        """
        🔑 Получение аргументов для формы
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        # Если передан ID сотрудника, добавляем его в kwargs
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            kwargs['employee_id'] = employee_id

        return kwargs

    def form_valid(self, form):
        """
        ✅ Обработка успешной валидации формы
        """
        # Сохраняем выбранные СИЗ
        issued_items = form.save()

        if issued_items:
            # Получаем информацию о сотруднике для сообщения
            employee = form.cleaned_data['employee']

            # Формируем сообщение об успешной выдаче
            success_message = f"✅ Сотруднику {employee.full_name_dative} выдано {len(issued_items)} СИЗ"
            messages.success(self.request, success_message)

            # Перенаправляем на личную карточку сотрудника
            return redirect('directory:siz:siz_personal_card', employee_id=employee.pk)
        else:
            # Если ничего не выбрано, выводим предупреждение
            messages.warning(self.request, "⚠️ Не выбрано ни одного СИЗ для выдачи")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        📊 Получение контекста для шаблона
        """
        context = super().get_context_data(**kwargs)

        # Добавляем заголовок страницы
        context['title'] = "Выдача СИЗ"

        # Если передан ID сотрудника, добавляем его в контекст
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
                context['employee'] = employee
                context['title'] = f"Выдача СИЗ для {employee.full_name_nominative}"
            except Employee.DoesNotExist:
                pass

        return context


class SIZPersonalCardView(LoginRequiredMixin, DetailView):
    """
    👤 Представление личной карточки учета СИЗ
    """
    model = Employee
    template_name = 'directory/siz_issued/personal_card.html'
    context_object_name = 'employee'

    def get_object(self, queryset=None):
        """
        🔍 Получение объекта сотрудника по ID
        """
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(
            Employee.objects.select_related('position', 'organization', 'subdivision', 'department'),
            pk=employee_id
        )

    def get_context_data(self, **kwargs):
        """
        📊 Получение контекста для шаблона
        """
        context = super().get_context_data(**kwargs)
        employee = self.object

        # Добавляем заголовок страницы
        context['title'] = f"Личная карточка учета СИЗ - {employee.full_name_nominative}"

        # Получаем нормы СИЗ для должности сотрудника
        if employee.position:
            # Группируем нормы по условиям
            norms = SIZNorm.objects.filter(
                position=employee.position
            ).select_related('siz').order_by('condition', 'order', 'siz__name')

            # Разделяем нормы на базовые (без условий) и по условиям
            base_norms = norms.filter(condition='')

            # Получаем уникальные условия
            conditions = norms.exclude(condition='').values_list('condition', flat=True).distinct()

            # Формируем группы норм по условиям
            condition_groups = []
            for condition in conditions:
                condition_norms = norms.filter(condition=condition)
                condition_groups.append({
                    'name': condition,
                    'norms': condition_norms
                })

            context['base_norms'] = base_norms
            context['condition_groups'] = condition_groups

        # Получаем выданные СИЗ для сотрудника
        issued_items = SIZIssued.objects.filter(
            employee=employee
        ).select_related('siz').order_by('-issue_date')

        # Разделяем на активные (не возвращенные) и возвращенные
        active_items = issued_items.filter(is_returned=False)
        returned_items = issued_items.filter(is_returned=True)

        context['issued_items'] = issued_items
        context['active_items'] = active_items
        context['returned_items'] = returned_items

        return context


class SIZIssueReturnView(LoginRequiredMixin, UpdateView):
    """
    🔙 Представление для возврата выданного СИЗ
    """
    model = SIZIssued
    form_class = SIZIssueReturnForm
    template_name = 'directory/siz_issued/return_form.html'

    def get_success_url(self):
        """
        🔄 URL для перенаправления после успешного возврата
        """
        # Перенаправляем на личную карточку сотрудника
        return reverse('directory:siz:siz_personal_card', kwargs={'employee_id': self.object.employee.pk})

    def form_valid(self, form):
        """
        ✅ Обработка успешной валидации формы
        """
        response = super().form_valid(form)

        # Формируем сообщение об успешном возврате
        employee = self.object.employee
        siz = self.object.siz
        success_message = f"✅ СИЗ '{siz.name}' от {self.object.issue_date.strftime('%d.%m.%Y')} успешно возвращено"
        messages.success(self.request, success_message)

        return response

    def get_context_data(self, **kwargs):
        """
        📊 Получение контекста для шаблона
        """
        context = super().get_context_data(**kwargs)

        # Добавляем заголовок страницы и информацию о возвращаемом СИЗ
        issued_item = self.object
        context['title'] = f"Возврат СИЗ"
        context['siz_name'] = issued_item.siz.name
        context['issue_date'] = issued_item.issue_date
        context['employee'] = issued_item.employee

        return context


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