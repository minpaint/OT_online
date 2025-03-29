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
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from directory.models import Employee
from directory.models.document_template import DocumentTemplate
from directory.forms.document_forms import DocumentPreviewForm
from directory.utils.docx_generator import (
    generate_internship_order, generate_admission_order
    # Закомментировали ненужные импорты:
    # generate_knowledge_protocol, generate_doc_familiarization
)


class DocumentPreviewView(LoginRequiredMixin, FormView):
    """
    Представление для предпросмотра и редактирования документа перед генерацией
    """
    template_name = 'directory/documents/document_preview.html'
    form_class = DocumentPreviewForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document_data = json.loads(self.request.POST.get('document_data', '{}'))
        document_type = self.request.POST.get('document_type')
        employee_id = document_data.get('employee_id')

        if employee_id:
            employee = get_object_or_404(Employee, id=employee_id)
            context['employee'] = employee

        context['document_data'] = document_data
        context['document_type'] = document_type

        if document_type == 'internship_order':
            context['title'] = _('Предпросмотр распоряжения о стажировке')
        elif document_type == 'admission_order':
            context['title'] = _('Предпросмотр распоряжения о допуске к самостоятельной работе')

        return context

    def form_valid(self, form):
        document_data = json.loads(form.cleaned_data['document_data'])
        document_type = form.cleaned_data['document_type']
        employee_id = form.cleaned_data['employee_id']

        employee = get_object_or_404(Employee, id=employee_id)

        # Генерируем соответствующий документ
        generated_doc = None
        if document_type == 'internship_order':
            generated_doc = generate_internship_order(
                employee,
                self.request.user,
                document_data
            )
            success_message = _('Распоряжение о стажировке успешно сгенерировано')
        elif document_type == 'admission_order':
            generated_doc = generate_admission_order(
                employee,
                self.request.user,
                document_data
            )
            success_message = _('Распоряжение о допуске к самостоятельной работе успешно сгенерировано')
        # Закомментируем пока неиспользуемые типы документов
        # elif document_type == 'knowledge_protocol':
        #     generated_doc = generate_knowledge_protocol(
        #         employee,
        #         self.request.user,
        #         document_data
        #     )
        #     success_message = _('Протокол проверки знаний успешно сгенерирован')
        # elif document_type == 'doc_familiarization':
        #     generated_doc = generate_doc_familiarization(
        #         employee,
        #         self.request.user,
        #         document_data
        #     )
        #     success_message = _('Лист ознакомления с документами успешно сгенерирован')

        if generated_doc:
            messages.success(self.request, success_message)
            return redirect('directory:documents:document_detail', pk=generated_doc.id)
        else:
            messages.error(self.request, _('Ошибка при генерации документа'))
            return self.form_invalid(form)


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
            return context

        preview_data = json.loads(preview_data_json)
        context['preview_data'] = preview_data

        # Если есть данные о сотруднике, добавляем их в контекст
        if preview_data and len(preview_data) > 0:
            employee_id = preview_data[0].get('employee_id')
            if employee_id:
                context['employee'] = get_object_or_404(Employee, id=employee_id)

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

        preview_data = json.loads(preview_data_json)

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
            employee = get_object_or_404(Employee, id=employee_id)

            # Генерируем документ в зависимости от типа
            generated_doc = None

            if doc_type == 'internship_order':
                generated_doc = generate_internship_order(
                    employee,
                    request.user,
                    document_data
                )
            elif doc_type == 'admission_order':
                generated_doc = generate_admission_order(
                    employee,
                    request.user,
                    document_data
                )
            # Закомментируем пока неиспользуемые типы документов
            # elif doc_type == 'knowledge_protocol':
            #     generated_doc = generate_knowledge_protocol(
            #         employee,
            #         request.user,
            #         document_data
            #     )
            # elif doc_type == 'doc_familiarization':
            #     generated_doc = generate_doc_familiarization(
            #         employee,
            #         request.user,
            #         document_data
            #     )

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


@method_decorator(login_required, name='dispatch')
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