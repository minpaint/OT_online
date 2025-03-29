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
    InternshipOrderForm, AdmissionOrderForm, DocumentPreviewForm
)
from directory.utils.docx_generator import (
    prepare_employee_context, generate_internship_order, generate_admission_order
)
from directory.utils.declension import get_initials_from_name


class InternshipOrderFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о стажировке
    """
    template_name = 'directory/documents/internship_order_form.html'
    form_class = InternshipOrderForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

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
            'fio_dative': context['fio_dative'],
            'position_dative': context['position_dative'],
            'department': context['department'],
            'subdivision': context['subdivision'],
            'internship_duration': context.get('internship_duration', '2'),
            'order_date': timezone.now().date(),
            'location': context.get('location', 'г. Минск'),
            'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
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
        context['employee'] = employee
        context['title'] = _('Распоряжение о стажировке')
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
                'document_type': 'internship_order',
                'employee_id': employee.id
            })

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'internship_order',
                    'employee': employee,
                    'title': _('Предпросмотр распоряжения о стажировке')
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
            custom_context = form.cleaned_data
            generated_doc = generate_internship_order(
                employee,
                self.request.user,
                custom_context
            )

            if generated_doc:
                messages.success(
                    self.request,
                    _('Распоряжение о стажировке успешно сгенерировано')
                )
                return redirect('directory:documents:document_detail', pk=generated_doc.id)
            else:
                messages.error(
                    self.request,
                    _('Ошибка при генерации документа')
                )
                return self.form_invalid(form)

        return super().form_valid(form)


class AdmissionOrderFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о допуске к самостоятельной работе
    """
    template_name = 'directory/documents/admission_order_form.html'
    form_class = AdmissionOrderForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

        # Подготавливаем начальные данные для формы на основе данных сотрудника
        context = prepare_employee_context(employee)

        # Получаем информацию о руководителе (тот же, что и для стажировки)
        internship_leader = None
        if employee.department:
            internship_leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()

        # Заполняем начальные данные формы
        initial.update({
            'organization_name': context['organization_name'],
            'fio_nominative': context['fio_nominative'],
            'position_nominative': context['position_nominative'],
            'department': context['department'],
            'subdivision': context['subdivision'],
            'order_date': timezone.now().date(),
            'location': context.get('location', 'г. Минск'),
            'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
        })

        # Добавляем информацию о руководителе, если он найден
        if internship_leader:
            initial.update({
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
        context['employee'] = employee
        context['title'] = _('Распоряжение о допуске к самостоятельной работе')
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
                'document_type': 'admission_order',
                'employee_id': employee.id
            })

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'admission_order',
                    'employee': employee,
                    'title': _('Предпросмотр распоряжения о допуске к самостоятельной работе')
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
            custom_context = form.cleaned_data
            generated_doc = generate_admission_order(
                employee,
                self.request.user,
                custom_context
            )

            if generated_doc:
                messages.success(
                    self.request,
                    _('Распоряжение о допуске к самостоятельной работе успешно сгенерировано')
                )
                return redirect('directory:documents:document_detail', pk=generated_doc.id)
            else:
                messages.error(
                    self.request,
                    _('Ошибка при генерации документа')
                )
                return self.form_invalid(form)

        return super().form_valid(form)