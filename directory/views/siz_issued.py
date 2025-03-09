# 📁 directory/views/siz_issued.py
from django.views.generic import CreateView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse  # 🆕 Добавлен HttpResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone  # 🆕 Добавлен импорт timezone
from django.template.loader import get_template  # 🆕 Добавлен импорт get_template
from io import BytesIO  # 🆕 Добавлен импорт BytesIO
from xhtml2pdf import pisa  # 🆕 Добавлен импорт pisa

from directory.models import Employee, SIZIssued
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
                from directory.models.siz import SIZNorm
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
            from directory.models.siz import SIZNorm
            norms = SIZNorm.objects.filter(
                position=self.object.position
            ).select_related('siz')

            # Базовые нормы (без условий)
            context['base_norms'] = norms.filter(condition='')

            # Нормы по условиям
            conditions = list(set(norm.condition for norm in norms if norm.condition))
            condition_groups = []

            for condition in conditions:
                condition_norms = [norm for norm in norms if norm.condition == condition]
                if condition_norms:
                    condition_groups.append({
                        'name': condition,
                        'norms': condition_norms
                    })

            context['condition_groups'] = condition_groups

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
def export_personal_card_pdf(request, employee_id):
    """
    📄 Экспорт личной карточки учета СИЗ в формате PDF

    Args:
        request: HttpRequest объект
        employee_id: ID сотрудника

    Returns:
        HttpResponse с вложенным PDF-файлом
    """
    from directory.utils.pdf import render_to_pdf

    employee = get_object_or_404(Employee, pk=employee_id)

    # Получаем все выданные сотруднику СИЗ
    issued_items = SIZIssued.objects.filter(
        employee=employee
    ).select_related('siz').order_by('-issue_date')

    # Получаем нормы СИЗ для должности сотрудника
    base_norms = []
    condition_groups = []

    if employee.position:
        from directory.models.siz import SIZNorm
        norms = SIZNorm.objects.filter(
            position=employee.position
        ).select_related('siz')

        # Базовые нормы (без условий)
        base_norms = list(norms.filter(condition=''))

        # Нормы по условиям
        conditions = list(set(norm.condition for norm in norms if norm.condition))

        for condition in conditions:
            condition_norms = [norm for norm in norms if norm.condition == condition]
            if condition_norms:
                condition_groups.append({
                    'name': condition,
                    'norms': condition_norms
                })

    # Подготовка контекста для шаблона
    context = {
        'employee': employee,
        'issued_items': issued_items,
        'base_norms': base_norms,
        'condition_groups': condition_groups,
        'today': timezone.now().date(),
    }

    # Формирование имени файла для скачивания
    filename = f"personal_card_{employee.full_name_nominative.replace(' ', '_')}.pdf"

    # Рендеринг PDF с использованием нашей утилиты
    return render_to_pdf(
        template_path='directory/siz_issued/personal_card_pdf.html',
        context=context,
        filename=filename,
        as_attachment=True
    )