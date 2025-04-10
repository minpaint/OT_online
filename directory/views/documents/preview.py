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

# --- Обновленные импорты --- 
from directory.document_generators.base import get_document_template, generate_docx_from_template # Базовые функции
from directory.document_generators.order_generator import generate_all_orders # Генератор распоряжений
# Импорты specific generators (protocol, familiarization, etc.) are needed if used directly
from directory.document_generators.protocol_generator import generate_knowledge_protocol
from directory.document_generators.familiarization_generator import generate_familiarization_document
from directory.document_generators.siz_card_generator import generate_siz_card # Хотя вызывается иначе
from directory.document_generators.ot_card_generator import generate_personal_ot_card
from directory.document_generators.journal_example_generator import generate_journal_example
# --- --- --- 

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
            document_context = doc_data.get('document_data', {})

            # Обновляем данные документа, если есть изменения
            if doc_type in updated_data:
                document_context.update(updated_data[doc_type])

            # Получаем сотрудника
            try:
                employee = get_object_or_404(Employee, id=employee_id)
            except:
                messages.error(request, gettext(f'Не удалось найти сотрудника для документа типа {doc_type}'))
                continue

            generated_doc = None # Сюда будем записывать результат генерации

            # --- Вызываем соответствующий генератор --- 
            try:
                if doc_type == 'all_orders':
                    generated_doc = generate_all_orders(employee, request.user, document_context)
                elif doc_type == 'knowledge_protocol':
                    generated_doc = generate_knowledge_protocol(employee, request.user, document_context)
                elif doc_type == 'doc_familiarization':
                    # Нужно получить список документов, если он не передан в document_context
                    doc_list = document_context.get('documents_list') # Предполагаем, что он может быть в контексте
                    generated_doc = generate_familiarization_document(employee, doc_list, request.user, document_context)
                elif doc_type == 'siz_card':
                    has_siz_card = True # Обрабатываем отдельно ниже
                    continue
                elif doc_type == 'personal_ot_card':
                    generated_doc = generate_personal_ot_card(employee, request.user, document_context)
                elif doc_type == 'journal_example':
                    generated_doc = generate_journal_example(employee, request.user, document_context)
                else:
                    # Попытка сгенерировать с помощью базового генератора, если тип не известен
                    template = get_document_template(doc_type, employee)
                    if template:
                        logger.info(f"Используется базовый генератор для типа: {doc_type}")
                        generated_doc = generate_docx_from_template(template, document_context, employee, request.user)
                    else:
                        logger.warning(f"Не найден шаблон или генератор для типа документа: {doc_type}")
                        messages.warning(request, gettext(f'Не найден шаблон или генератор для типа документа: {doc_type}'))
                        continue

            except Exception as e:
                error_msg = gettext(f'Ошибка при генерации документа типа {doc_type}:') + f' {str(e)}'
                logger.error(error_msg, exc_info=True)
                messages.error(request, error_msg)
                continue # Переходим к следующему документу
            # --- --- --- 

            if generated_doc and isinstance(generated_doc, GeneratedDocument): # Убедимся, что это нужный объект
                generated_documents.append(generated_doc)
                # Добавляем файл в список для архивирования
                doc_path = os.path.join(settings.MEDIA_ROOT, str(generated_doc.document_file))
                if os.path.exists(doc_path):
                    file_name = os.path.basename(generated_doc.document_file.name)
                    files_to_archive.append((doc_path, file_name))
                    logger.info(f"Добавлен файл в архив: {doc_path}, размер: {os.path.getsize(doc_path)} bytes")
                else:
                    logger.warning(f"Файл не найден по пути: {doc_path}")
            elif generated_doc: # Если вернулось что-то другое (например, HttpResponse для СИЗ, хотя мы его пропускаем)
                logger.warning(f"Генератор для {doc_type} вернул неожиданный тип: {type(generated_doc)}")

        # Если нужно добавить карточку СИЗ и хотя бы один сотрудник был найден
        if has_siz_card and employee_id: 
            try:
                # Получаем сотрудника еще раз (на случай, если цикл не выполнился)
                employee = get_object_or_404(Employee, id=employee_id)
                logger.info(f"Начинаем генерацию карточки СИЗ для сотрудника ID: {employee_id}")
                
                # Вызываем генератор карточки СИЗ (который вызывает excel_export)
                # Предполагаем, что custom_context для СИЗ находится в updated_data
                siz_context = updated_data.get('siz_card', {}) 
                siz_response = generate_siz_card(employee, request.user, siz_context)
                
                if siz_response and isinstance(siz_response, HttpResponse) and siz_response.status_code == 200:
                    logger.info(f"Карточка СИЗ (Excel) успешно сгенерирована.")
                    # Создаем временный файл для Excel
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                        for chunk in siz_response.streaming_content if hasattr(siz_response, 'streaming_content') else [siz_response.content]:
                            tmp_file.write(chunk)
                    
                    tmp_file_size = os.path.getsize(tmp_file.name)
                    if tmp_file_size > 0:
                        excel_filename = f'siz_card_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                        files_to_archive.append((tmp_file.name, excel_filename))
                        logger.info(f"Добавлен Excel файл СИЗ в архив: {tmp_file.name}, размер: {tmp_file_size} bytes")
                        
                        # Можно опционально создать запись GeneratedDocument для Excel файла
                        # template = get_document_template('siz_card', employee) ... 
                        # siz_document = GeneratedDocument(...) ... siz_document.save()
                    else:
                         logger.error("Файл Excel СИЗ создан с нулевым размером!")
                         messages.warning(request, gettext('Сгенерированный файл карточки СИЗ пуст.'))
                else:
                     error_msg = gettext('Не удалось сгенерировать карточку СИЗ (Excel).')
                     if siz_response:
                         error_msg += f" Статус: {siz_response.status_code}"
                     logger.error(error_msg)
                     messages.warning(request, error_msg)

            except Exception as e:
                error_msg = gettext('Ошибка при генерации карточки СИЗ:') + ' ' + str(e)
                logger.error(f"Ошибка СИЗ: {str(e)}", exc_info=True)
                messages.warning(request, error_msg)

        # Очищаем данные предпросмотра из сессии
        if 'preview_data' in request.session:
            del request.session['preview_data']

        # --- Обработка результатов --- 
        if len(files_to_archive) > 1:
            # Создаем директорию для временных файлов, если она не существует
            tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_archives') # Изменил имя папки
            os.makedirs(tmp_dir, exist_ok=True)

            # Создаем временный файл для архива
            zip_filename = f'documents_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            zip_path = os.path.join(tmp_dir, zip_filename)

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
                    # Попытка добавить хотя бы существующие файлы
                    if any(os.path.exists(fp) and os.path.getsize(fp) > 0 for fp, _ in files_to_archive):
                        logger.warning("Архив пуст, но есть сгенерированные файлы. Возможно, ошибка архивации.")
                    else:
                         raise ValueError("Создан пустой или некорректный архив, и нет валидных файлов для добавления")

                logger.info(f"Архив создан: {zip_path}, размер: {os.path.getsize(zip_path)} bytes")

                # Отправляем архив пользователю
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()

                response = HttpResponse(zip_content, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                response['Content-Length'] = len(zip_content)
                
                success_msg = gettext('Успешно сгенерировано и заархивировано документов: {}').format(len(files_to_archive))
                messages.success(request, success_msg)
                
                # Удаляем архив после отправки
                os.unlink(zip_path)

                # Очищаем временные файлы (только те, что в tmp_dir)
                for file_path, _ in files_to_archive:
                    if file_path.startswith(tempfile.gettempdir()) or file_path.startswith(tmp_dir): 
                        try:
                            os.unlink(file_path)
                        except OSError as e:
                            logger.error(f"Не удалось удалить временный файл {file_path}: {e}")
                            
                return response
            except Exception as e:
                logger.error(f"Ошибка при создании или отправке архива: {str(e)}", exc_info=True)
                messages.error(request, gettext('Ошибка при создании архива: ') + str(e))
                 # Если архив не создан, но есть файлы, предложим скачать первый
                if len(generated_documents) >= 1:
                     messages.info(request, gettext('Попробуйте скачать документы по одному.'))
                     return redirect('directory:documents:document_detail', pk=generated_documents[0].id)
                return self.get(request, *args, **kwargs) # Возврат на страницу предпросмотра

        # Если сгенерирован только один документ (не СИЗ)
        elif len(generated_documents) == 1:
            messages.success(request, gettext('Документ успешно сгенерирован'))
            return redirect('directory:documents:document_detail', pk=generated_documents[0].id)
        
        # Если была только карточка СИЗ (и она успешно добавлена в files_to_archive)
        elif len(files_to_archive) == 1 and has_siz_card:
            file_path, file_name = files_to_archive[0]
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                if len(file_content) == 0:
                    raise ValueError("Файл пуст")
                
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' # Excel
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                response['Content-Length'] = len(file_content)
                
                messages.success(request, gettext('Карточка СИЗ успешно сгенерирована'))
                # Удаляем временный файл
                if file_path.startswith(tempfile.gettempdir()):
                    os.unlink(file_path)
                return response
            except Exception as e:
                logger.error(f"Ошибка при отправке файла СИЗ: {file_path}, ошибка: {str(e)}")
                messages.error(request, gettext('Ошибка при отправке файла СИЗ: ') + str(e))
                return self.get(request, *args, **kwargs)
        else:
            # Ситуация, когда не было сгенерировано ни одного документа или файла
            if not messages.get_messages(request):
                 messages.error(request, gettext('Не удалось сгенерировать ни один из выбранных документов'))
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
        updated = False
        for doc_data in preview_data:
            if doc_data.get('document_type') == doc_type:
                if 'document_data' not in doc_data: doc_data['document_data'] = {}
                doc_data['document_data'][field_name] = field_value
                updated = True
                break
        
        if not updated:
             return JsonResponse({'success': False, 'error': f'Документ типа {doc_type} не найден в данных предпросмотра'})

        # Сохраняем обновленные данные в сессию
        # Используем default=str для обработки несериализуемых объектов, например, дат
        request.session['preview_data'] = json.dumps(preview_data, default=str) 
        request.session.modified = True # Убедимся, что сессия сохранится

        return JsonResponse({'success': True})
    except json.JSONDecodeError:
         return JsonResponse({'success': False, 'error': 'Ошибка декодирования данных сессии'})
    except Exception as e:
        logger.error(f"Ошибка в update_document_data: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})