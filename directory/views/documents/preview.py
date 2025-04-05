"""
👁️ Представления для предпросмотра документов

Содержит представления для предпросмотра и редактирования документов перед генерацией.
"""
import json
import os
import tempfile
import zipfile
import datetime
import logging
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.translation import gettext
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from directory.models import Employee
from directory.models.document_template import DocumentTemplate
from directory.models import GeneratedDocument
from directory.forms.document_forms import DocumentPreviewForm
from directory.utils.docx_generator import (
    generate_all_orders, get_document_template, generate_document_from_template
)

# Настройка логирования
logger = logging.getLogger(__name__)


class DocumentsPreviewView(LoginRequiredMixin, TemplateView):
    """
    Представление для предпросмотра всех выбранных документов перед генерацией
    """
    template_name = 'directory/documents/documents_preview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем данные предпросмотра из сессии
        preview_data_json = self.request.session.get('preview_data')
        if not preview_data_json:
            messages.error(self.request, gettext('Не найдены данные для предпросмотра документов'))
            context['no_data'] = True
            return context

        try:
            preview_data = json.loads(preview_data_json)
            context['preview_data'] = preview_data
        except json.JSONDecodeError:
            messages.error(self.request, gettext('Ошибка при чтении данных предпросмотра'))
            context['no_data'] = True
            return context

        # Если есть данные о сотруднике, добавляем их в контекст
        if preview_data and len(preview_data) > 0:
            employee_id = preview_data[0].get('employee_id')
            if employee_id:
                try:
                    context['employee'] = get_object_or_404(Employee, id=employee_id)
                except:
                    messages.warning(self.request, gettext('Не удалось получить информацию о сотруднике'))

        # Получаем словарь соответствия типов документов их названиям
        document_types_dict = dict(DocumentTemplate.DOCUMENT_TYPES)
        context['document_types_dict'] = document_types_dict

        context['title'] = gettext('Предпросмотр документов')
        return context

    def post(self, request, *args, **kwargs):
        """
        Обработка POST-запроса для генерации документов
        """
        # Получаем данные предпросмотра из сессии
        preview_data_json = request.session.get('preview_data')
        if not preview_data_json:
            messages.error(request, gettext('Не найдены данные для генерации документов'))
            return redirect('directory:home')

        try:
            preview_data = json.loads(preview_data_json)
        except json.JSONDecodeError:
            messages.error(request, gettext('Ошибка при чтении данных для генерации документов'))
            return redirect('directory:home')

        # Получаем обновленные данные документов из формы
        updated_data = {}
        for key, value in request.POST.items():
            if key.startswith('document_data_'):
                parts = key.replace('document_data_', '').split('_', 1)
                if len(parts) == 2:
                    doc_type, field = parts
                    if doc_type not in updated_data:
                        updated_data[doc_type] = {}
                    updated_data[doc_type][field] = value

        # Генерируем все выбранные документы
        generated_documents = []
        files_to_archive = []
        has_siz_card = False
        employee_id = None

        for doc_data in preview_data:
            doc_type = doc_data.get('document_type')
            employee_id = doc_data.get('employee_id')
            document_data = doc_data.get('document_data', {})

            # Обновляем данные документа, если есть изменения
            if doc_type in updated_data:
                document_data.update(updated_data[doc_type])

            # Получаем сотрудника
            try:
                employee = get_object_or_404(Employee, id=employee_id)
            except:
                messages.error(request, gettext('Не удалось найти сотрудника'))
                continue

            # Запоминаем, есть ли карточка СИЗ среди выбранных документов
            if doc_type == 'siz_card':
                has_siz_card = True
                continue  # Пропускаем генерацию карточки СИЗ на этом этапе

            # Генерируем документ в зависимости от типа
            generated_doc = None

            if doc_type == 'all_orders':
                # Генерация комбинированного распоряжения
                generated_doc = generate_all_orders(
                    employee,
                    request.user,
                    document_data
                )
            elif doc_type in ['knowledge_protocol', 'doc_familiarization']:
                # Используем общую функцию для генерации документа по шаблону
                template = get_document_template(doc_type)
                if template:
                    generated_doc = generate_document_from_template(
                        template,
                        employee,
                        request.user,
                        document_data
                    )

            if generated_doc:
                generated_documents.append(generated_doc)
                # Добавляем файл в список для архивирования
                doc_path = os.path.join(settings.MEDIA_ROOT, str(generated_doc.document_file))
                if os.path.exists(doc_path):
                    file_name = os.path.basename(generated_doc.document_file.name)
                    files_to_archive.append((doc_path, file_name))
                    logger.info(f"Добавлен файл в архив: {doc_path}, размер: {os.path.getsize(doc_path)} bytes")
                else:
                    logger.warning(f"Файл не найден по пути: {doc_path}")

        # Если нужно добавить карточку СИЗ и хотя бы один сотрудник был найден
        if has_siz_card and employee_id:
            try:
                # Импортируем функцию только при необходимости
                from directory.views.siz_issued import export_personal_card_pdf

                # Создаем временный файл для сохранения PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    # Вызываем существующую функцию
                    pdf_response = export_personal_card_pdf(request, employee_id)

                    # Проверяем тип ответа
                    if hasattr(pdf_response, 'content'):
                        tmp_file.write(pdf_response.content)
                    elif hasattr(pdf_response, 'streaming_content'):
                        for chunk in pdf_response.streaming_content:
                            tmp_file.write(chunk)

                # Проверяем размер созданного файла
                tmp_file_size = os.path.getsize(tmp_file.name)
                logger.info(f"Создан PDF файл для СИЗ: {tmp_file.name}, размер: {tmp_file_size} bytes")

                # Убедимся, что файл не пустой
                if tmp_file_size == 0:
                    logger.error("PDF файл СИЗ создан с нулевым размером!")
                    raise ValueError("PDF файл СИЗ имеет нулевой размер")

                # Добавляем файл в список для архивирования
                pdf_filename = f'siz_card_{employee.full_name_nominative}.pdf'
                files_to_archive.append((tmp_file.name, pdf_filename))

                # Создаем запись о сгенерированном документе для PDF
                template = DocumentTemplate.objects.filter(
                    document_type='siz_card',
                    is_active=True
                ).order_by('-id').first()

                if not template:
                    template = DocumentTemplate.objects.create(
                        document_type='siz_card',
                        name='Карточка учета СИЗ',
                        description='Карточка учета средств индивидуальной защиты',
                        is_active=True
                    )

                # Создаем запись в базе данных
                siz_document = GeneratedDocument(
                    template=template,
                    employee=employee,
                    created_by=request.user
                )
                siz_document.document_file.save(pdf_filename, pdf_response)
                siz_document.save()

                generated_documents.append(siz_document)

            except Exception as e:
                error_msg = gettext('Ошибка при генерации карточки СИЗ:') + ' ' + str(e)
                logger.error(f"Ошибка СИЗ: {str(e)}")
                messages.warning(request, error_msg)

        # Очищаем данные предпросмотра из сессии
        if 'preview_data' in request.session:
            del request.session['preview_data']

        # Если нужно создать архив (несколько файлов)
        if len(files_to_archive) > 1:
            # Создаем директорию для временных файлов, если она не существует
            tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)

            # Создаем временный файл для архива
            zip_filename = f'documents_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            zip_path = os.path.join(tmp_dir, zip_filename)

            # Улучшенная версия создания архива
            try:
                # Создаем архив и добавляем в него файлы
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path, file_name in files_to_archive:
                        # Проверяем существование и размер файла
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            zipf.write(file_path, file_name)
                            logger.info(f"Файл {file_path} добавлен в архив как {file_name}")
                        else:
                            logger.warning(f"Пропущен файл {file_path}: файл не существует или пуст")

                # Проверяем, что архив создался и не пустой
                if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                    raise ValueError("Создан пустой или некорректный архив")

                logger.info(f"Архив создан: {zip_path}, размер: {os.path.getsize(zip_path)} bytes")

                # Отправляем архив пользователю
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()

                response = HttpResponse(zip_content, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                response['Content-Length'] = len(zip_content)

                # Очищаем временные файлы
                try:
                    os.unlink(zip_path)
                    for file_path, _ in files_to_archive:
                        if file_path.startswith(tmp_dir):  # Удаляем только временные файлы
                            os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Ошибка при удалении временных файлов: {str(e)}")

                success_msg = gettext('Успешно сгенерировано документов: {}').format(len(files_to_archive))
                messages.success(request, success_msg)

                return response
            except Exception as e:
                logger.error(f"Ошибка при создании архива: {str(e)}")
                messages.error(request, gettext('Ошибка при создании архива: ') + str(e))
                return self.get(request, *args, **kwargs)

        # Если сгенерирован только один документ
        elif len(generated_documents) == 1:
            messages.success(request, gettext('Документ успешно сгенерирован'))
            return redirect('directory:documents:document_detail', pk=generated_documents[0].id)

        # Если есть временные файлы, но не было создано документов в базе
        elif len(files_to_archive) == 1:
            file_path, file_name = files_to_archive[0]
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                    # Проверка содержимого файла
                    if len(file_content) == 0:
                        raise ValueError("Файл пуст")

                    content_type = 'application/pdf' if file_name.endswith('.pdf') else 'application/octet-stream'
                    response = HttpResponse(file_content, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                    response['Content-Length'] = len(file_content)

                # Удаляем временный файл
                try:
                    if file_path.startswith(os.path.join(settings.MEDIA_ROOT, 'tmp')):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Ошибка при удалении временного файла: {str(e)}")

                messages.success(request, gettext('Документ успешно сгенерирован'))
                return response
            except Exception as e:
                logger.error(f"Ошибка при отправке файла: {file_path}, ошибка: {str(e)}")
                messages.error(request, gettext('Ошибка при отправке файла: ') + str(e))
                return self.get(request, *args, **kwargs)

        else:
            messages.error(request, gettext('Не удалось сгенерировать документы'))
            return self.get(request, *args, **kwargs)


@login_required
@require_POST
def update_document_data(request):
    """
    Обработчик AJAX-запроса для обновления данных документа в сессии
    """
    try:
        # Получаем данные из запроса
        doc_type = request.POST.get('doc_type')
        field_name = request.POST.get('field_name')
        field_value = request.POST.get('field_value')

        # Получаем данные предпросмотра из сессии
        preview_data_json = request.session.get('preview_data')
        if not preview_data_json:
            return JsonResponse({'success': False, 'error': 'Не найдены данные для предпросмотра'})

        preview_data = json.loads(preview_data_json)

        # Обновляем данные в соответствующем документе
        for doc_data in preview_data:
            if doc_data.get('document_type') == doc_type:
                doc_data['document_data'][field_name] = field_value
                break

        # Сохраняем обновленные данные в сессию
        request.session['preview_data'] = json.dumps(preview_data, default=str)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})