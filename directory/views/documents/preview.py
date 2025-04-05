"""
👁️ Представления для предпросмотра документов

Содержит представления для предпросмотра и редактирования документов перед генерацией.
"""
import json
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from directory.models import Employee
from directory.models.document_template import DocumentTemplate
from directory.forms.document_forms import DocumentPreviewForm
from directory.utils.docx_generator import (
    generate_all_orders, generate_siz_card,
    get_document_template, generate_document_from_template
)


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
            messages.error(self.request, _('Не найдены данные для предпросмотра документов'))
            context['no_data'] = True
            return context

        try:
            preview_data = json.loads(preview_data_json)
            context['preview_data'] = preview_data
        except json.JSONDecodeError:
            messages.error(self.request, _('Ошибка при чтении данных предпросмотра'))
            context['no_data'] = True
            return context

        # Если есть данные о сотруднике, добавляем их в контекст
        if preview_data and len(preview_data) > 0:
            employee_id = preview_data[0].get('employee_id')
            if employee_id:
                try:
                    context['employee'] = get_object_or_404(Employee, id=employee_id)
                except:
                    messages.warning(self.request, _('Не удалось получить информацию о сотруднике'))

        # Получаем словарь соответствия типов документов их названиям
        document_types_dict = dict(DocumentTemplate.DOCUMENT_TYPES)
        context['document_types_dict'] = document_types_dict

        context['title'] = _('Предпросмотр документов')
        return context

    def post(self, request, *args, **kwargs):
        """
        Обработка POST-запроса для генерации документов
        """
        # Получаем данные предпросмотра из сессии
        preview_data_json = request.session.get('preview_data')
        if not preview_data_json:
            messages.error(request, _('Не найдены данные для генерации документов'))
            return redirect('directory:home')

        try:
            preview_data = json.loads(preview_data_json)
        except json.JSONDecodeError:
            messages.error(request, _('Ошибка при чтении данных для генерации документов'))
            return redirect('directory:home')

        # Получаем обновленные данные документов из формы
        updated_data = {}
        for key, value in request.POST.items():
            if key.startswith('document_data_'):
                doc_type, field = key.replace('document_data_', '').split('_', 1)
                if doc_type not in updated_data:
                    updated_data[doc_type] = {}
                updated_data[doc_type][field] = value

        # Генерируем все выбранные документы
        generated_documents = []

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
                messages.error(request, _('Не удалось найти сотрудника'))
                continue

            # Генерируем документ в зависимости от типа
            generated_doc = None

            if doc_type == 'all_orders':
                generated_doc = generate_all_orders(
                    employee,
                    request.user,
                    document_data
                )
            elif doc_type == 'siz_card':
                generated_doc = generate_siz_card(
                    employee,
                    request.user,
                    document_data
                )
            elif doc_type == 'knowledge_protocol' or doc_type == 'doc_familiarization':
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

        # Очищаем данные предпросмотра из сессии
        if 'preview_data' in request.session:
            del request.session['preview_data']

        # Сообщаем об успешной генерации
        if generated_documents:
            messages.success(
                request,
                _('Успешно сгенерировано документов: {}').format(len(generated_documents))
            )

            # Если сгенерирован только один документ, перенаправляем на его страницу
            if len(generated_documents) == 1:
                return redirect('directory:documents:document_detail', pk=generated_documents[0].id)

            # Иначе перенаправляем на список документов
            return redirect('directory:documents:document_list')
        else:
            messages.error(request, _('Не удалось сгенерировать документы'))
            return self.get(request, *args, **kwargs)


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