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
from directory.forms.document_forms import (
    AllOrdersForm, SIZCardForm, DocumentPreviewForm
)
from directory.utils.docx_generator import (
    prepare_employee_context, generate_all_orders
)
from directory.utils.declension import get_initials_from_name


class AllOrdersFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о стажировке и допуске к работе
    """
    template_name = 'directory/documents/all_orders_form.html'
    form_class = AllOrdersForm

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
                'fio_dative': context['fio_dative'],  # или можно использовать именительный падеж
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

        # Если нажата кнопка предпросмотра
        if 'preview' in self.request.POST:
            # Собираем данные для предпросмотра
            document_data = form.cleaned_data
            document_data['employee_id'] = employee.id
            document_data['order_type'] = order_type

            # Передаем данные форме предпросмотра
            preview_form = DocumentPreviewForm(initial={
                'document_data': json.dumps(document_data, default=str),
                'document_type': 'all_orders',  # Используем единый тип для всех распоряжений
                'employee_id': employee.id
            })

            # Определяем заголовок для страницы предпросмотра
            if order_type == 'internship_order':
                title = _('Предпросмотр распоряжения о стажировке')
            else:  # admission_order
                title = _('Предпросмотр распоряжения о допуске к самостоятельной работе')

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'all_orders',
                    'employee': employee,
                    'title': title
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
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

        return super().form_valid(form)


class SIZCardFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы карточки учета СИЗ
    """
    template_name = 'directory/documents/siz_card_form.html'
    form_class = SIZCardForm

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

        # Если нажата кнопка предпросмотра
        if 'preview' in self.request.POST:
            # Собираем данные для предпросмотра
            document_data = form.cleaned_data
            document_data['employee_id'] = employee.id

            # Передаем данные форме предпросмотра
            preview_form = DocumentPreviewForm(initial={
                'document_data': json.dumps(document_data, default=str),
                'document_type': 'siz_card',
                'employee_id': employee.id
            })

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'siz_card',
                    'employee': employee,
                    'title': _('Предпросмотр карточки учета СИЗ')
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
            # Здесь будет вызов функции generate_siz_card
            from directory.utils.docx_generator import generate_siz_card

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

        return super().form_valid(form)