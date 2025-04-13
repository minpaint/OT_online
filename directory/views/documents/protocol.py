# directory/views/documents/protocol.py

from django import forms
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
import logging

from directory.models import Employee
from directory.document_generators.protocol_generator import generate_knowledge_protocol
from directory.services.commission_service import find_appropriate_commission, get_commission_members_formatted

# Настройка логирования
logger = logging.getLogger(__name__)


class ProtocolForm(forms.Form):
    """
    Форма для указания параметров протокола проверки знаний.
    Без возможности выбора комиссии (комиссия определяется автоматически).
    """
    ticket_number = forms.IntegerField(
        label="Номер билета",
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    test_result = forms.ChoiceField(
        label="Результат проверки знаний",
        choices=[
            ('прошел', 'Прошел'),
            ('не прошел', 'Не прошел')
        ],
        required=True,
        initial='прошел',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)

        # Устанавливаем номер билета по умолчанию на основе ID сотрудника
        if employee and employee.id:
            self.fields['ticket_number'].initial = employee.id % 20 + 1


class KnowledgeProtocolCreateView(LoginRequiredMixin, FormView):
    """
    Представление для создания протокола проверки знаний
    с автоматическим выбором комиссии.
    """
    template_name = 'directory/documents/protocol_form.html'
    form_class = ProtocolForm

    def get_employee(self):
        """Получает сотрудника из параметров URL"""
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_form_kwargs(self):
        """Передаем сотрудника в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.get_employee()
        return kwargs

    def get_context_data(self, **kwargs):
        """Добавляет данные о сотруднике и комиссии в контекст"""
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()

        context['employee'] = employee
        context['title'] = f'Протокол проверки знаний: {employee.full_name_nominative}'

        # Находим подходящую комиссию автоматически
        commission = find_appropriate_commission(employee)

        if commission:
            context['commission'] = commission

            # Получаем и форматируем участников комиссии для предпросмотра
            commission_data = get_commission_members_formatted(commission)
            context['commission_data'] = commission_data

            # Проверяем полноту состава комиссии
            has_chairman = bool(commission_data.get('chairman'))
            has_secretary = bool(commission_data.get('secretary'))
            has_members = len(commission_data.get('members', [])) > 0

            # Если состав неполный, выводим предупреждение
            if not (has_chairman and has_secretary and has_members):
                missing = []
                if not has_chairman:
                    missing.append('председатель')
                if not has_secretary:
                    missing.append('секретарь')
                if not has_members:
                    missing.append('члены комиссии')

                context['warning_message'] = f"Внимание! В комиссии отсутствуют: {', '.join(missing)}."
        else:
            context['warning_message'] = "Не найдена подходящая комиссия для сотрудника."

        # Добавляем информацию о выбранных ранее типах документов (если есть)
        if 'selected_document_types' in self.request.session:
            context['selected_document_types'] = self.request.session['selected_document_types']

        return context

    def form_valid(self, form):
        """Обрабатывает отправку формы"""
        employee = self.get_employee()
        ticket_number = form.cleaned_data['ticket_number']
        test_result = form.cleaned_data['test_result']

        # Находим подходящую комиссию автоматически
        commission = find_appropriate_commission(employee)

        if not commission:
            messages.error(self.request, 'Не найдена подходящая комиссия для сотрудника')
            return self.form_invalid(form)

        # Получаем данные о комиссии
        commission_data = get_commission_members_formatted(commission)

        # Проверяем полноту состава комиссии
        has_chairman = bool(commission_data.get('chairman'))
        has_secretary = bool(commission_data.get('secretary'))
        has_members = len(commission_data.get('members', [])) > 0

        if not (has_chairman and has_secretary and has_members):
            missing = []
            if not has_chairman:
                missing.append('председатель')
            if not has_secretary:
                missing.append('секретарь')
            if not has_members:
                missing.append('члены комиссии')

            messages.warning(
                self.request,
                f"В комиссии '{commission.name}' отсутствуют: {', '.join(missing)}. "
                f"Протокол будет создан с неполным составом комиссии."
            )

        # Создаем контекст для передачи в генератор протокола
        custom_context = {
            'commission_name': commission_data.get('commission_name', ''),
            'ticket_number': ticket_number,
            'test_result': test_result,
        }

        # Добавляем информацию о председателе
        chairman = commission_data.get('chairman', {})
        if chairman:
            custom_context.update({
                'chairman_name': chairman.get('name', ''),
                'chairman_position': chairman.get('position', ''),
                'chairman_name_initials': chairman.get('name_initials', ''),
                'chairman_formatted': chairman.get('formatted', '')
            })

        # Добавляем информацию о секретаре
        secretary = commission_data.get('secretary', {})
        if secretary:
            custom_context.update({
                'secretary_name': secretary.get('name', ''),
                'secretary_position': secretary.get('position', ''),
                'secretary_name_initials': secretary.get('name_initials', ''),
                'secretary_formatted': secretary.get('formatted', '')
            })

        # Добавляем информацию о членах комиссии
        members = commission_data.get('members', [])
        custom_context['commission_members'] = [m.get('formatted', '') for m in members]

        # Добавляем полную информацию о всех участниках для шаблона
        custom_context['members_formatted'] = commission_data.get('members_formatted', [])

        # Генерируем протокол
        generated_doc = generate_knowledge_protocol(
            employee=employee,
            user=self.request.user,
            custom_context=custom_context
        )

        if generated_doc:
            messages.success(self.request, 'Протокол проверки знаний успешно сгенерирован')

            # Проверяем, нужно ли сгенерировать другие документы
            if 'selected_document_types' in self.request.session:
                selected_types = self.request.session['selected_document_types']

                # Если был выбран только протокол, удаляем информацию из сессии и перенаправляем на документ
                if len(selected_types) == 1 and selected_types[0] == 'knowledge_protocol':
                    del self.request.session['selected_document_types']
                    return redirect('directory:documents:document_detail', pk=generated_doc.id)

                # Если были выбраны и другие документы, перенаправляем на генерацию остальных документов
                selected_types.remove('knowledge_protocol')
                self.request.session['selected_document_types'] = selected_types

                messages.info(
                    self.request,
                    'Сейчас будет выполнена генерация остальных выбранных документов'
                )

                # Здесь должен быть код для генерации остальных документов или переход к соответствующему URL
                return redirect('directory:documents:generate_multiple', employee_id=employee.id)

            return redirect('directory:documents:document_detail', pk=generated_doc.id)
        else:
            messages.error(self.request, 'Ошибка при генерации протокола проверки знаний')
            return self.form_invalid(form)