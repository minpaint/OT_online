"""
🔍 Представления для выбора типов документов

Содержит представления для выбора типов документов, которые нужно сгенерировать.
"""
import json
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.forms.document_forms import DocumentSelectionForm
from directory.utils.docx_generator import prepare_employee_context
from .utils import (
    get_internship_leader_position, get_internship_leader_name,
    get_internship_leader_initials, get_director_info,
    get_commission_members, get_safety_instructions,
    get_employee_documents
)


class DocumentSelectionView(LoginRequiredMixin, FormView):
    """
    Представление для выбора типов документов для генерации
    """
    template_name = 'directory/documents/document_selection.html'
    form_class = DocumentSelectionForm

    def get_initial(self):
        initial = super().get_initial()
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            initial['employee_id'] = employee_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            context['employee'] = get_object_or_404(Employee, id=employee_id)
        context['title'] = _('Выбор типов документов')
        return context

    def form_valid(self, form):
        try:
            employee_id = form.cleaned_data['employee_id']
            document_types = form.cleaned_data.get('document_types', [])

            # Проверяем, пришли ли типы документов
            if not document_types:
                # Проверяем альтернативные имена полей, которые могут прийти из формы
                for field_name in ['document_type', 'document-types']:
                    if field_name in form.cleaned_data:
                        document_types = form.cleaned_data[field_name]
                        if not isinstance(document_types, list):
                            document_types = [document_types]
                        break

                # Если все еще нет типов документов, смотрим в request.POST
                if not document_types:
                    document_types = self.request.POST.getlist('document_types')

            # Если все еще нет типов документов, выдаем ошибку
            if not document_types:
                messages.error(self.request, _("Необходимо выбрать хотя бы один тип документа"))
                return self.form_invalid(form)

            employee = get_object_or_404(Employee, id=employee_id)

            # Подготавливаем базовый контекст на основе данных сотрудника
            base_context = prepare_employee_context(employee)

            # Создаем предпросмотры для всех выбранных типов документов
            preview_data = []

            for doc_type in document_types:
                # Создаем контекст для каждого типа документа
                context = self._prepare_document_context(doc_type, employee, base_context)

                # Добавляем информацию о типе документа и данные для предпросмотра
                preview_data.append({
                    'document_type': doc_type,
                    'document_data': context,
                    'employee_id': employee_id
                })

            # Сохраняем данные предпросмотра в сессию для использования на странице предпросмотра
            self.request.session['preview_data'] = json.dumps(preview_data, default=str)

            # Перенаправляем на страницу предпросмотра
            return HttpResponseRedirect(reverse('directory:documents:documents_preview'))
        except Exception as e:
            messages.error(self.request, f"Ошибка при обработке формы: {str(e)}")
            return self.form_invalid(form)

    def _prepare_document_context(self, document_type, employee, base_context):
        """
        Подготавливает контекст для определенного типа документа

        Args:
            document_type: Тип документа (строка)
            employee: Объект сотрудника Employee
            base_context: Базовый контекст с данными сотрудника

        Returns:
            dict: Контекст документа
        """
        context = base_context.copy()
        missing_data = []

        # Добавляем дополнительные данные в зависимости от типа документа
        if document_type == 'internship_order':
            # Данные для распоряжения о стажировке
            internship_data = {
                'order_number': '',  # Номер распоряжения (пользователь должен ввести)
            }

            # Период стажировки
            if hasattr(employee.position, 'internship_period_days') and employee.position.internship_period_days:
                internship_data['internship_duration'] = employee.position.internship_period_days
            else:
                internship_data['internship_duration'] = 2
                missing_data.append('Период стажировки не указан в должности')

            # Информация о руководителе стажировки
            leader_position, position_success = get_internship_leader_position(employee)
            if not position_success:
                missing_data.append('Не найден руководитель стажировки')

            leader_name, name_success = get_internship_leader_name(employee)
            if not name_success:
                missing_data.append('Не найдено ФИО руководителя стажировки')

            leader_initials, initials_success = get_internship_leader_initials(employee)
            if not initials_success:
                missing_data.append('Не найдены инициалы руководителя стажировки')

            internship_data.update({
                'head_of_internship_position': leader_position,
                'head_of_internship_name': leader_name,
                'head_of_internship_name_initials': leader_initials,
            })

            # Информация о директоре (должна храниться в организации)
            director_info, director_success = get_director_info(employee.organization)
            if not director_success:
                missing_data.append('Не найдена информация о директоре')

            internship_data.update({
                'director_position': director_info['position'],
                'director_name': director_info['name'],
            })

            context.update(internship_data)

        elif document_type == 'admission_order':
            # Данные для распоряжения о допуске к самостоятельной работе
            admission_data = {
                'order_number': '',  # Номер распоряжения (пользователь должен ввести)
            }

            # Информация о директоре
            director_info, director_success = get_director_info(employee.organization)
            if not director_success:
                missing_data.append('Не найдена информация о директоре')

            admission_data.update({
                'director_position': director_info['position'],
                'director_name': director_info['name'],
            })

            # Используем того же руководителя, что и для стажировки
            leader_initials, initials_success = get_internship_leader_initials(employee)
            if not initials_success:
                missing_data.append('Не найдены инициалы руководителя')

            admission_data['head_of_internship_name_initials'] = leader_initials

            context.update(admission_data)

        elif document_type == 'knowledge_protocol':
            # Данные для протокола проверки знаний
            protocol_data = {
                'protocol_number': '',  # Номер протокола (пользователь должен ввести)
                'knowledge_result': 'удовлетворительные',
            }

            # Члены комиссии
            commission_members, commission_success = get_commission_members(employee)
            if not commission_success:
                missing_data.append('Не найдены члены комиссии')

            protocol_data['commission_members'] = commission_members

            # Инструкции по охране труда
            safety_instructions, instructions_success = get_safety_instructions(employee)
            if not instructions_success:
                missing_data.append('Не найдены инструкции по охране труда')

            protocol_data['safety_instructions'] = safety_instructions

            context.update(protocol_data)

        elif document_type == 'doc_familiarization':
            # Данные для листа ознакомления с документами
            familiarization_data = {
                'familiarization_date': base_context.get('order_date', ''),
            }

            # Документы для ознакомления
            documents_list, documents_success = get_employee_documents(employee)
            if not documents_success:
                missing_data.append('Не найдены документы для ознакомления')

            familiarization_data['documents_list'] = documents_list

            context.update(familiarization_data)

        # Добавляем информацию о недостающих данных в контекст
        context['missing_data'] = missing_data
        context['has_missing_data'] = len(missing_data) > 0

        return context