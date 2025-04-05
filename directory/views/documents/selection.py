# D:\YandexDisk\OT_online\directory\views\documents\selection.py
"""
🔍 Представления для выбора типов документов

Содержит представления для выбора типов документов, которые нужно сгенерировать.
"""
import json
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.models.document_template import DocumentTemplate
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

    def _get_document_type_display(self, doc_type):
        """
        Получает название типа документа для отображения
        """
        for type_code, type_name in DocumentTemplate.DOCUMENT_TYPES:
            if type_code == doc_type:
                return type_name
        return doc_type

    def form_valid(self, form):
        try:
            employee_id = form.cleaned_data.get('employee_id')
            if not employee_id and 'employee_id' in self.kwargs:
                employee_id = self.kwargs['employee_id']

            if not employee_id:
                messages.error(self.request, _("Не указан сотрудник"))
                return self.form_invalid(form)

            document_types = form.cleaned_data.get('document_types', [])

            if not document_types:
                messages.error(self.request, _("Не выбран ни один тип документа"))
                return self.form_invalid(form)

            employee = get_object_or_404(Employee, id=employee_id)

            # Подготавливаем базовый контекст на основе данных сотрудника
            base_context = prepare_employee_context(employee)

            # Создаем предпросмотры для выбранных типов документов
            preview_data = []

            for doc_type in document_types:
                # Создаем контекст для типа документа
                context = self._prepare_document_context(doc_type, employee, base_context)
                context['employee_id'] = employee_id  # Добавляем ID сотрудника в контекст

                # Добавляем информацию о типе документа и данные для предпросмотра
                preview_data.append({
                    'document_type': doc_type,
                    'document_data': context,
                    'employee_id': employee_id
                })

            # Проверяем, есть ли данные для предпросмотра
            if not preview_data:
                messages.error(self.request, _("Не удалось подготовить данные для предпросмотра"))
                return self.form_invalid(form)

            # Сохраняем данные предпросмотра в сессию
            self.request.session['preview_data'] = json.dumps(preview_data, default=str)

            # Отладочная информация в сессию
            self.request.session['debug_info'] = {
                'employee_id': employee_id,
                'document_types': document_types,
                'preview_data_length': len(preview_data)
            }

            # Проверяем, есть ли недостающие данные в документах
            has_missing_data = any(
                data.get('document_data', {}).get('has_missing_data', False)
                for data in preview_data
            )

            # Если есть недостающие данные, предупреждаем пользователя
            if has_missing_data:
                for data in preview_data:
                    doc_data = data.get('document_data', {})
                    missing = doc_data.get('missing_data', [])
                    if missing:
                        doc_type_display = self._get_document_type_display(data.get('document_type'))
                        message = _(f"⚠️ В документе '{doc_type_display}' отсутствуют данные: {', '.join(missing)}")
                        messages.warning(self.request, message)

                # Добавляем общее предупреждение
                messages.warning(
                    self.request,
                    _("⚠️ В документах отсутствуют некоторые данные. "
                      "Вы можете добавить их на странице предпросмотра перед генерацией.")
                )

            # Перенаправляем на страницу предпросмотра
            return redirect('directory:documents:documents_preview')

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
        missing_data = context.get('missing_data', []).copy()

        # Добавляем дополнительные данные в зависимости от типа документа
        if document_type == 'all_orders':
            # Данные для распоряжений о стажировке (объединенный шаблон)
            order_data = {
                'order_number': '',  # Номер распоряжения (пользователь должен ввести)
            }

            # Период стажировки
            if hasattr(employee.position, 'internship_period_days') and employee.position.internship_period_days:
                order_data['internship_duration'] = employee.position.internship_period_days
            else:
                order_data['internship_duration'] = 2
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

            order_data.update({
                'head_of_internship_position': leader_position,
                'head_of_internship_name': leader_name,
                'head_of_internship_name_initials': leader_initials,
            })

            # Информация о директоре (должна храниться в организации)
            director_info, director_success = get_director_info(employee.organization)
            if not director_success:
                missing_data.append('Не найдена информация о директоре')

            order_data.update({
                'director_position': director_info['position'],
                'director_name': director_info['name'],
            })

            context.update(order_data)

        elif document_type == 'siz_card':
            # Данные для карточки учета СИЗ
            from directory.models import SIZNorm

            # Получаем базовые нормы СИЗ для должности
            if employee.position:
                base_norms = SIZNorm.objects.filter(position=employee.position, condition='').select_related('siz')
                if not base_norms.exists():
                    missing_data.append('Не найдены базовые нормы СИЗ для должности')
            else:
                missing_data.append('Не указана должность для определения норм СИЗ')

            # Проверяем наличие данных о размерах
            if not employee.height:
                missing_data.append('Не указан рост сотрудника')
            if not employee.clothing_size:
                missing_data.append('Не указан размер одежды сотрудника')
            if not employee.shoe_size:
                missing_data.append('Не указан размер обуви сотрудника')

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

        # Обновляем информацию о недостающих данных в контексте
        context['missing_data'] = missing_data
        context['has_missing_data'] = len(missing_data) > 0

        return context