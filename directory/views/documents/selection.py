from typing import Optional
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
import os
import tempfile
import zipfile
import logging
import datetime

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.forms.document_forms import DocumentSelectionForm
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
        generated_documents = []
        files_to_archive = []

        logger.info(f"Начинается генерация документов для {employee.full_name_nominative}, типы: {document_types}")

        # Функция проверки шаблонов (оставлена для примера, можно убрать если не нужна)
        def check_template_file(doc_type_check, employee_check):
            template = get_document_template(doc_type_check, employee_check)
            if not template:
                logger.error(f"Шаблон для типа {doc_type_check} не найден!")
                return False
            logger.info(f"Найден шаблон для {doc_type_check}: {template.name}, ID: {template.id}")
            # analyze_template(template.id) # Можно раскомментировать для отладки переменных
            return True

        for doc_type in document_types:
            # Проверяем шаблон перед генерацией (опционально)
            # if not check_template_file(doc_type, employee):
            #     messages.warning(self.request, f"Пропущен документ типа {doc_type}: шаблон не найден.")
            #     continue

            # Генерируем документ с помощью соответствующего генератора
            try:
                generated_doc = self._generate_document(doc_type, employee)
                if generated_doc and isinstance(generated_doc, GeneratedDocument) and hasattr(generated_doc,
                                                                                              'document_file'):
                    generated_documents.append(generated_doc)
                    # Добавляем файл в список для архивирования
                    file_path = generated_doc.document_file.path  # Используем path для прямого пути
                    if os.path.exists(file_path):
                        file_name = os.path.basename(generated_doc.document_file.name)
                        files_to_archive.append((file_path, file_name))
                        logger.info(f"Добавлен файл в архив: {file_path}")
                    else:
                        logger.warning(f"Файл не найден по пути: {file_path}")
                elif generated_doc:
                    logger.warning(f"Генератор для {doc_type} вернул неожиданный тип: {type(generated_doc)}")
                # Если generated_doc is None, значит была ошибка внутри генератора
                # (он должен залогировать и вернуть None)

            except Exception as e:
                logger.error(f"Критическая ошибка при вызове генератора для типа {doc_type}: {str(e)}", exc_info=True)
                messages.warning(self.request, f"Ошибка при генерации документа типа {doc_type}: {str(e)}")
                continue  # Переходим к следующему документу

        # --- Создание и отправка архива ---
        if not files_to_archive:
            messages.error(self.request, "Не удалось сгенерировать ни один документ для добавления в архив")
            return self.form_invalid(form)

        try:
            # Создаем директорию для временных файлов
            tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_archives')
            os.makedirs(tmp_dir, exist_ok=True)

            # Создаем имя файла для архива
            zip_filename = f'documents_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            zip_path = os.path.join(tmp_dir, zip_filename)

            # Создаем архив
            added_files_count = 0
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, file_name in files_to_archive:
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        zipf.write(file_path, file_name)
                        added_files_count += 1
                        logger.info(f"Файл {file_path} добавлен в архив как {file_name}")
                    else:
                        logger.warning(f"Файл {file_path} не существует или пуст, пропускаем")

            # Проверяем, добавился ли хотя бы один файл в архив
            if added_files_count == 0:
                raise ValueError("Ни один файл не был добавлен в архив.")

            # Проверяем архив на наличие и размер
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                raise ValueError("Созданный архив пуст или отсутствует, хотя файлы для добавления были.")

            # Отправляем архив пользователю
            with open(zip_path, 'rb') as f:
                zip_content = f.read()

            response = HttpResponse(zip_content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

            # Сообщение об успехе
            messages.success(self.request, f"Успешно сгенерировано и добавлено в архив документов: {added_files_count}")

            # Удаляем архив после отправки
            os.unlink(zip_path)

            return response

        except Exception as e:
            logger.error(f"Ошибка при создании или отправке архива: {str(e)}", exc_info=True)
            messages.error(self.request, f"Ошибка при создании архива: {str(e)}")
            return self.form_invalid(form)

    def _generate_document(self, doc_type, employee) -> Optional[GeneratedDocument]:
        """Вызывает соответствующий генератор для документа типа doc_type"""
        generator_map = {
            'all_orders': generate_all_orders,
            'knowledge_protocol': generate_knowledge_protocol,
            'doc_familiarization': generate_familiarization_document,
            'personal_ot_card': generate_personal_ot_card,
            'journal_example': generate_journal_example,
            'siz_card': generate_siz_card_docx,  # Добавили генератор DOCX для СИЗ
        }

        generator_func = generator_map.get(doc_type)

        if generator_func:
            logger.info(f"Вызов генератора {generator_func.__name__} для типа {doc_type}")
            # Передаем пользователя из self.request
            # Для generate_familiarization_document может потребоваться document_list, но здесь его нет
            # Если он нужен, логику нужно усложнить
            if doc_type == 'doc_familiarization':
                # document_list=None - будет получен внутри генератора
                return generator_func(employee=employee, user=self.request.user, document_list=None)
            else:
                return generator_func(employee=employee, user=self.request.user)
        else:
            logger.error(f"Генератор для типа документа '{doc_type}' не найден в _generate_document")
            return None