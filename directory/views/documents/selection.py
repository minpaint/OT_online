from typing import Optional
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
import os
import io
import tempfile
import zipfile
import logging
import datetime

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, DocumentGenerationLog
from directory.forms.document_forms import DocumentSelectionForm
from directory.utils.declension import get_initials_from_name
# --- Обновленные импорты ---
from directory.document_generators.base import get_document_template  # Базовая функция для получения шаблона
from directory.utils.docx_generator import analyze_template  # Для проверки шаблона
from directory.document_generators.order_generator import generate_all_orders
from directory.document_generators.protocol_generator import generate_knowledge_protocol
from directory.document_generators.familiarization_generator import generate_familiarization_document
from directory.document_generators.ot_card_generator import generate_personal_ot_card
from directory.document_generators.journal_example_generator import generate_journal_example
from directory.document_generators.siz_card_docx_generator import generate_siz_card_docx  # Импорт для DOCX карточки СИЗ
# --- --- ---

from django.conf import settings

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
    5. Для всех подрядчиков добавляем Личную карточку по ОТ

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

    # Получаем флаг договора подряда
    is_contractor = getattr(employee, 'is_contractor', False)

    # Проверяем срок стажировки и договор подряда
    internship_period = getattr(employee.position, 'internship_period_days', 0)

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

    if has_siz_norms:
        document_types.append('siz_card')

    # Если есть договор подряда, добавляем Личную карточку по ОТ
    if is_contractor:
        document_types.append('personal_ot_card')

    logger.info(f"Автоматически выбранные типы документов для {employee.full_name_nominative}: {document_types}")
    # Убираем дубликаты на всякий случай
    return list(set(document_types))


class DocumentSelectionView(LoginRequiredMixin, FormView):
    """
    Представление для выбора типов документов и прямой генерации архива
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

                # Добавляем информацию о правилах выбора документов
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

        context['title'] = 'Выбор типов документов'
        return context

    def form_valid(self, form):
        # Получаем ID сотрудника и типы документов
        employee_id = form.cleaned_data.get('employee_id')
        document_types = form.cleaned_data.get('document_types', [])

        if not employee_id:
            messages.error(self.request, "Не указан сотрудник")
            return self.form_invalid(form)

        if not document_types:
            messages.error(self.request, "Не выбран ни один тип документа")
            return self.form_invalid(form)

        # Получаем сотрудника
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            messages.error(self.request, "Сотрудник не найден")
            return self.form_invalid(form)

        # Генерируем все выбранные документы и собираем их для архива
        files_to_archive = []  # Список кортежей (content, filename)

        logger.info(f"Начинается генерация документов для {employee.full_name_nominative}, типы: {document_types}")

        for doc_type in document_types:
            # Генерируем документ с помощью соответствующего генератора
            try:
                result = self._generate_document(doc_type, employee)
                if result and isinstance(result, dict) and 'content' in result and 'filename' in result:
                    files_to_archive.append((result['content'], result['filename']))
                    logger.info(f"Сгенерирован документ: {result['filename']}")
                elif result:
                    logger.warning(f"Генератор для {doc_type} вернул неожиданный формат: {type(result)}")

            except Exception as e:
                logger.error(f"Критическая ошибка при вызове генератора для типа {doc_type}: {str(e)}", exc_info=True)
                messages.warning(self.request, f"Ошибка при генерации документа типа {doc_type}: {str(e)}")
                continue

        # --- Создание и отправка архива ---
        if not files_to_archive:
            messages.error(self.request, "Не удалось сгенерировать ни один документ для добавления в архив")
            return self.form_invalid(form)

        try:
            # Создаем архив в памяти
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for content, filename in files_to_archive:
                    zipf.writestr(filename, content)
                    logger.info(f"Файл {filename} добавлен в архив")

            zip_buffer.seek(0)

            # Формируем имя архива
            employee_initials = get_initials_from_name(employee.full_name_nominative)
            zip_filename = f"Документы_{employee_initials}.zip"

            # Отправляем архив пользователю
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            # Кодируем имя файла для поддержки кириллицы
            from urllib.parse import quote
            encoded_filename = quote(zip_filename)
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"

            # Записываем в лог факт генерации документов
            try:
                DocumentGenerationLog.objects.create(
                    employee=employee,
                    document_types=document_types,
                    created_by=self.request.user if self.request.user.is_authenticated else None
                )
                logger.info(f"Записан лог генерации документов для {employee.full_name_nominative}")
            except Exception as log_error:
                logger.warning(f"Не удалось записать лог генерации: {str(log_error)}")

            # Сообщение об успехе
            messages.success(self.request, f"Успешно сгенерировано документов: {len(files_to_archive)}")

            return response

        except Exception as e:
            logger.error(f"Ошибка при создании или отправке архива: {str(e)}", exc_info=True)
            messages.error(self.request, f"Ошибка при создании архива: {str(e)}")
            return self.form_invalid(form)

    def _generate_document(self, doc_type, employee) -> Optional[dict]:
        """Вызывает соответствующий генератор для документа типа doc_type.
        Возвращает словарь с 'content' и 'filename' или None."""
        generator_map = {
            'all_orders': generate_all_orders,
            'knowledge_protocol': generate_knowledge_protocol,
            'doc_familiarization': generate_familiarization_document,
            'personal_ot_card': generate_personal_ot_card,
            'journal_example': generate_journal_example,
            'siz_card': generate_siz_card_docx,
        }

        generator_func = generator_map.get(doc_type)

        if generator_func:
            logger.info(f"Вызов генератора {generator_func.__name__} для типа {doc_type}")
            if doc_type == 'doc_familiarization':
                return generator_func(employee=employee, user=self.request.user, document_list=None)
            else:
                return generator_func(employee=employee, user=self.request.user)
        else:
            logger.error(f"Генератор для типа документа '{doc_type}' не найден в _generate_document")
            return None