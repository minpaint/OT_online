"""
📝 Представления для форм создания документов

Содержит представления для форм создания различных типов документов.
"""
import json
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone

from directory.models import Employee
# Удалены импорты несуществующих форм (AllOrdersForm, SIZCardForm, DocumentPreviewForm)

from directory.utils.docx_generator import (
    prepare_employee_context, generate_all_orders, generate_siz_card
)
from directory.utils.declension import get_initials_from_name


class AllOrdersFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о стажировке и допуске к работе
    """
    template_name = 'directory/documents/all_orders_form.html'
    # Поскольку AllOrdersForm отсутствует, нужно создать базовую форму или временно указать другую
    form_class = None  # Будет заменено на актуальную форму или переопределено в get_form_class

    def get_form_class(self):
        """Возвращает класс формы для использования"""
        from django import forms

        # Создаем форму динамически
        class TempAllOrdersForm(forms.Form):
            """Временная базовая форма для распоряжений"""
            organization_name = forms.CharField(label=_("Наименование организации"))
            order_date = forms.DateField(label=_("Дата распоряжения"))

        return TempAllOrdersForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_order_type(self):
        """Получает тип распоряжения из параметров запроса"""
        return self.kwargs.get('order_type', 'internship_order')

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

        # Определяем тип распоряжения
        order_type = self.get_order_type()

        # Подготавливаем начальные данные для формы на основе данных сотрудника
        context = prepare_employee_context(employee)

        # Получаем информацию о руководителе стажировки
        internship_leader = None
        if employee.department:
            internship_leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()

        # Заполняем начальные данные формы
        initial.update({
            'organization_name': context['organization_name'],
            'department': context['department'],
            'subdivision': context['subdivision'],
            'order_date': timezone.now().date(),
            'location': context.get('location', 'г. Минск'),
            'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
        })

        # Добавляем специфичные поля в зависимости от типа распоряжения
        if order_type == 'internship_order':
            initial.update({
                'fio_dative': context['fio_dative'],
                'position_dative': context['position_dative'],
                'internship_duration': context.get('internship_duration', '2'),
            })
        else:  # admission_order
            initial.update({
                'fio_dative': context['fio_dative'],
                'position_dative': context['position_dative'],
            })

        # Добавляем информацию о руководителе стажировки, если он найден
        if internship_leader:
            initial.update({
                'head_of_internship_position': internship_leader.position.position_name if internship_leader.position else "",
                'head_of_internship_name': internship_leader.full_name_nominative,
                'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            })

        # Добавляем информацию о директоре (в данном случае берем из организации)
        if employee.organization:
            initial['director_name'] = "И.И. Коржов"  # Здесь можно получать из данных организации
            initial['director_position'] = "Директор"

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        order_type = self.get_order_type()

        context['employee'] = employee

        # Устанавливаем заголовок в зависимости от типа распоряжения
        if order_type == 'internship_order':
            context['title'] = _('Распоряжение о стажировке')
            context['order_type'] = 'internship_order'
        else:  # admission_order
            context['title'] = _('Распоряжение о допуске к самостоятельной работе')
            context['order_type'] = 'admission_order'

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.get_employee()
        return kwargs

    def form_valid(self, form):
        employee = self.get_employee()
        order_type = self.get_order_type()

        # Прямая генерация документа без предпросмотра
        custom_context = form.cleaned_data
        custom_context['order_type'] = order_type  # Добавляем тип распоряжения в контекст

        generated_doc = generate_all_orders(
            employee,
            self.request.user,
            custom_context
        )

        if generated_doc:
            # Определяем сообщение об успехе в зависимости от типа распоряжения
            if order_type == 'internship_order':
                success_message = _('Распоряжение о стажировке успешно сгенерировано')
            else:  # admission_order
                success_message = _('Распоряжение о допуске к работе успешно сгенерировано')

            messages.success(self.request, success_message)
            return redirect('directory:documents:document_detail', pk=generated_doc.id)
        else:
            messages.error(self.request, _('Ошибка при генерации документа'))
            return self.form_invalid(form)


class SIZCardFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы карточки учета СИЗ
    """
    template_name = 'directory/documents/siz_card_form.html'
    # Поскольку SIZCardForm отсутствует, нужно создать базовую форму или временно указать другую
    form_class = None  # Будет заменено на актуальную форму или переопределено в get_form_class

    def get_form_class(self):
        """Возвращает класс формы для использования"""
        from django import forms

        # Создаем форму динамически
        class TempSIZCardForm(forms.Form):
            """Временная базовая форма для карточки СИЗ"""
            organization_name = forms.CharField(label=_("Наименование организации"))
            employee_name = forms.CharField(label=_("ФИО сотрудника"))

        return TempSIZCardForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

        # Подготавливаем начальные данные для формы
        context = prepare_employee_context(employee)

        # Заполняем начальные данные формы
        initial.update({
            'organization_name': context['organization_name'],
            'employee_name': context['fio_nominative'],
            'position_name': context['position_nominative'] if 'position_nominative' in context else "",
        })

        # Добавляем размеры СИЗ, если они есть у сотрудника
        if hasattr(employee, 'height'):
            initial['height'] = employee.height
        if hasattr(employee, 'clothing_size'):
            initial['clothing_size'] = employee.clothing_size
        if hasattr(employee, 'shoe_size'):
            initial['shoe_size'] = employee.shoe_size
        if hasattr(employee, 'headgear_size'):
            initial['headgear_size'] = employee.headgear_size
        if hasattr(employee, 'respirator_size'):
            initial['respirator_size'] = employee.respirator_size
        if hasattr(employee, 'gloves_size'):
            initial['gloves_size'] = employee.gloves_size

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        context['employee'] = employee
        context['title'] = _('Карточка учета СИЗ')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.get_employee()
        return kwargs

    def form_valid(self, form):
        employee = self.get_employee()

        # Прямая генерация документа без предпросмотра
        custom_context = form.cleaned_data
        generated_doc = generate_siz_card(
            employee,
            self.request.user,
            custom_context
        )

        if generated_doc:
            messages.success(
                self.request,
                _('Карточка учета СИЗ успешно сгенерирована')
            )
            return redirect('directory:documents:document_detail', pk=generated_doc.id)
        else:
            messages.error(
                self.request,
                _('Ошибка при генерации документа')
            )
            return self.form_invalid(form)