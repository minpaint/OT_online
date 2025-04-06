# directory/views/documents/selection.py
"""
🔍 Представления для выбора типов документов

Содержит представления для выбора типов документов, которые нужно сгенерировать.
"""
import json
import logging
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.models.document_template import DocumentTemplate
from directory.forms.document_forms import DocumentSelectionForm
from directory.utils.docx_generator import (
    generate_all_orders, generate_knowledge_protocol,
    generate_familiarization_document, generate_siz_card,
    generate_personal_ot_card, generate_journal_example
)

# Настройка логирования
logger = logging.getLogger(__name__)


def get_auto_selected_document_types(employee):
    """
    Автоматически определяет типы документов для генерации на основе данных сотрудника.

    Правила выбора:
    1. Если срок стажировки > 0 и нет договора подряда: Распоряжения стажировки + Протокол проверки знаний
    2. Если срок стажировки > 0 и есть договор подряда: только Протокол проверки знаний
    3. Если у должности есть связанные документы: Лист ознакомления
    4. Если у должности есть нормы СИЗ: Карточка учета СИЗ

    Args:
        employee (Employee): Объект сотрудника

    Returns:
        list: Список кодов типов документов для генерации
    """
    document_types = []

    # Проверяем наличие должности
    if not employee.position:
        logger.warning(f"У сотрудника {employee.full_name_nominative} не указана должность")
        return document_types

    # Проверяем срок стажировки и договор подряда
    internship_period = getattr(employee.position, 'internship_period_days', 0)
    is_contractor = getattr(employee, 'is_contractor', False)

    if internship_period > 0:
        # Если это не договор подряда, добавляем распоряжение о стажировке
        if not is_contractor:
            document_types.append('all_orders')

        # В любом случае добавляем протокол проверки знаний
        document_types.append('knowledge_protocol')

    # Проверяем связанные документы для должности
    has_documents = False
    if hasattr(employee.position, 'documents') and employee.position.documents.exists():
        has_documents = True
        document_types.append('doc_familiarization')

    # Проверяем наличие норм СИЗ
    has_siz_norms = False

    # Проверяем эталонные нормы СИЗ
    from directory.models.siz import SIZNorm
    if SIZNorm.objects.filter(position=employee.position).exists():
        has_siz_norms = True

    # Также можно проверить нормы, определенные непосредственно в должности
    # if hasattr(employee.position, 'siz_items') and employee.position.siz_items.exists():
    #     has_siz_norms = True

    if has_siz_norms:
        document_types.append('siz_card')

    logger.info(f"Автоматически выбранные типы документов для {employee.full_name_nominative}: {document_types}")

    return document_types


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

            # Получаем сотрудника
            try:
                employee = Employee.objects.get(id=employee_id)

                # Автоматически выбираем типы документов
                document_types = get_auto_selected_document_types(employee)
                initial['document_types'] = document_types

            except Employee.DoesNotExist:
                logger.error(f"Сотрудник с ID {employee_id} не найден")

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get('employee_id')

        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id)
                context['employee'] = employee

                # Добавляем информацию о правилах выбора документов для дебага
                context['internship_period'] = getattr(employee.position, 'internship_period_days',
                                                       0) if employee.position else 0
                context['is_contractor'] = getattr(employee, 'is_contractor', False)
                context['has_documents'] = hasattr(employee.position,
                                                   'documents') and employee.position.documents.exists() if employee.position else False

                # Проверяем наличие норм СИЗ
                from directory.models.siz import SIZNorm
                context['has_siz_norms'] = SIZNorm.objects.filter(
                    position=employee.position).exists() if employee.position else False

            except Employee.DoesNotExist:
                logger.error(f"Сотрудник с ID {employee_id} не найден")

        context['title'] = _('Выбор типов документов')
        return context

    def form_valid(self, form):
        # Получаем ID сотрудника и типы документов
        employee_id = form.cleaned_data.get('employee_id')
        document_types = form.cleaned_data.get('document_types', [])

        if not employee_id:
            messages.error(self.request, _("Не указан сотрудник"))
            return self.form_invalid(form)

        if not document_types:
            messages.error(self.request, _("Не выбран ни один тип документа"))
            return self.form_invalid(form)

        # Получаем сотрудника
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            messages.error(self.request, _("Сотрудник не найден"))
            return self.form_invalid(form)

        # Генерируем документы
        generated_documents = []

        for doc_type in document_types:
            generated_doc = self._generate_document(doc_type, employee)
            if generated_doc:
                generated_documents.append(generated_doc)

        # Если сгенерирован хотя бы один документ
        if generated_documents:
            # Если документ один, перенаправляем на его страницу
            if len(generated_documents) == 1:
                messages.success(self.request, _("Документ успешно сгенерирован"))
                return redirect('directory:documents:document_detail', pk=generated_documents[0].id)
            else:
                # Если документов несколько, перенаправляем на список документов
                messages.success(self.request, _("Документы успешно сгенерированы"))
                return redirect('directory:documents:document_list')
        else:
            messages.error(self.request, _("Не удалось сгенерировать документы"))
            return self.form_invalid(form)

    def _generate_document(self, doc_type, employee):
        """Генерирует документ указанного типа для сотрудника"""
        logger.info(f"Генерация документа типа {doc_type} для сотрудника {employee.full_name_nominative}")

        if doc_type == 'all_orders':
            return generate_all_orders(employee, self.request.user)
        elif doc_type == 'knowledge_protocol':
            return generate_knowledge_protocol(employee, self.request.user)
        elif doc_type == 'doc_familiarization':
            return generate_familiarization_document(employee, user=self.request.user)
        elif doc_type == 'siz_card':
            return generate_siz_card(employee, self.request.user)
        elif doc_type == 'personal_ot_card':
            return generate_personal_ot_card(employee, self.request.user)
        elif doc_type == 'journal_example':
            return generate_journal_example(employee, self.request.user)
        else:
            logger.error(f"Неизвестный тип документа: {doc_type}")
            return None