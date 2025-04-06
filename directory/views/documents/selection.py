from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
import os
import tempfile
import zipfile
import logging
import datetime

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.forms.document_forms import DocumentSelectionForm
from directory.utils.docx_generator import (
    generate_all_orders, generate_knowledge_protocol,
    generate_familiarization_document, generate_siz_card,
    generate_personal_ot_card, generate_journal_example
)
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

        # Генерируем документы и собираем их для архива
        generated_documents = []
        files_to_archive = []

        # ДОБАВЛЕННЫЙ КОД: логируем начало процесса генерации
        logger.info(f"Начинается генерация документов для типов: {document_types}")

        # ДОБАВЛЕННЫЙ КОД: проверка шаблонов документов
        def check_template_file(document_type, employee):
            """Проверка наличия и доступности шаблона документа"""
            from directory.utils.docx_generator import get_document_template, analyze_template

            template = get_document_template(document_type, employee)
            if not template:
                logger.error(f"Шаблон для типа {document_type} не найден!")
                return False

            logger.info(f"Найден шаблон для {document_type}: {template.name}, ID: {template.id}")

            # Анализируем шаблон для получения используемых переменных
            analyze_template(template.id)
            return True

        # Проверяем все шаблоны перед генерацией
        for doc_type in document_types:
            if doc_type != 'siz_card':  # Для карточки СИЗ шаблон не требуется
                check_template_file(doc_type, employee)

        has_siz_card = False

        for doc_type in document_types:
            # Обрабатываем карточку СИЗ отдельно
            if doc_type == 'siz_card':
                has_siz_card = True
                continue  # Будем обрабатывать отдельно ниже

            # Генерируем документ
            try:
                generated_doc = self._generate_document(doc_type, employee)
                if generated_doc and hasattr(generated_doc, 'document_file'):
                    generated_documents.append(generated_doc)
                    # Добавляем файл в список для архивирования
                    file_path = os.path.join(settings.MEDIA_ROOT, str(generated_doc.document_file))
                    if os.path.exists(file_path):
                        file_name = os.path.basename(generated_doc.document_file.name)
                        files_to_archive.append((file_path, file_name))
                        logger.info(f"Добавлен файл в архив: {file_path}")
                    else:
                        logger.warning(f"Файл не найден по пути: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при генерации документа типа {doc_type}: {str(e)}")
                messages.warning(self.request, f"Ошибка при генерации документа типа {doc_type}: {str(e)}")

        # Обрабатываем карточку СИЗ, если она была выбрана
        if has_siz_card:
            try:
                # Импортируем функцию только при необходимости
                from directory.views.siz_issued import export_personal_card_pdf

                # Создаем временный файл для PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    # Подготавливаем фиктивный request
                    from django.http import HttpRequest
                    fake_request = HttpRequest()
                    fake_request.user = self.request.user

                    # Вызываем существующую функцию генерации PDF
                    pdf_response = export_personal_card_pdf(fake_request, employee_id)

                    # Сохраняем содержимое PDF в файл
                    if hasattr(pdf_response, 'content'):
                        tmp_file.write(pdf_response.content)
                    elif hasattr(pdf_response, 'streaming_content'):
                        for chunk in pdf_response.streaming_content:
                            tmp_file.write(chunk)

                # Проверяем размер файла
                if os.path.getsize(tmp_file.name) > 0:
                    # Добавляем файл в список для архивирования
                    pdf_filename = f'siz_card_{employee.full_name_nominative}.pdf'
                    files_to_archive.append((tmp_file.name, pdf_filename))
                    logger.info(f"Добавлен PDF-файл СИЗ в архив: {tmp_file.name}")
                else:
                    logger.error("PDF-файл СИЗ имеет нулевой размер")
                    messages.warning(self.request, "Ошибка при генерации PDF-файла СИЗ: файл пуст")
            except Exception as e:
                logger.error(f"Ошибка при генерации карточки СИЗ: {str(e)}")
                messages.warning(self.request, f"Ошибка при генерации карточки СИЗ: {str(e)}")

        # Если нет файлов для архивирования, возвращаем ошибку
        if not files_to_archive:
            messages.error(self.request, "Не удалось сгенерировать ни один документ")
            return self.form_invalid(form)

        # Создаем архив с документами
        try:
            # Создаем директорию для временных файлов, если она не существует
            tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)

            # Создаем имя файла для архива
            zip_filename = f'documents_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            zip_path = os.path.join(tmp_dir, zip_filename)

            # Создаем архив
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, file_name in files_to_archive:
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        zipf.write(file_path, file_name)
                        logger.info(f"Файл {file_path} добавлен в архив как {file_name}")
                    else:
                        logger.warning(f"Файл {file_path} не существует или пуст, пропускаем")

            # Проверяем архив на наличие и размер
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                raise ValueError("Созданный архив пуст или отсутствует")

            # Отправляем архив пользователю
            with open(zip_path, 'rb') as f:
                zip_content = f.read()

            response = HttpResponse(zip_content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

            # Очищаем временные файлы
            try:
                # Удаляем временный архив
                os.unlink(zip_path)
                # Удаляем временный PDF для СИЗ, если он был создан
                for file_path, _ in files_to_archive:
                    if file_path.endswith('.pdf') and os.path.exists(file_path) and tmp_dir in file_path:
                        os.unlink(file_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временных файлов: {str(e)}")

            # Добавляем сообщение об успехе (оно будет показано после редиректа)
            messages.success(self.request, f"Успешно сгенерировано документов: {len(files_to_archive)}")

            return response

        except Exception as e:
            logger.error(f"Ошибка при создании архива: {str(e)}")
            messages.error(self.request, f"Ошибка при создании архива: {str(e)}")
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
        elif doc_type == 'personal_ot_card':
            return generate_personal_ot_card(employee, self.request.user)
        elif doc_type == 'journal_example':
            return generate_journal_example(employee, self.request.user)
        else:
            logger.error(f"Неизвестный тип документа: {doc_type}")
            return None