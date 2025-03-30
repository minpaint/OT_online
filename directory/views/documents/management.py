"""
📊 Представления для управления сгенерированными документами

Содержит представления для просмотра списка документов, 
деталей документа и скачивания документов.
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument


class GeneratedDocumentListView(LoginRequiredMixin, ListView):
    """
    Представление для списка сгенерированных документов
    """
    model = GeneratedDocument
    template_name = 'directory/documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        """
        Получение списка документов с возможностью фильтрации
        """
        queryset = super().get_queryset().select_related('template', 'employee', 'created_by')

        # Фильтрация по сотруднику
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # Фильтрация по типу документа
        doc_type = self.request.GET.get('type')
        if doc_type and doc_type != 'all':
            queryset = queryset.filter(template__document_type=doc_type)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        """
        Подготовка контекста для шаблона
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Сгенерированные документы')

        # Список сотрудников для фильтрации
        context['employees'] = Employee.objects.all()

        # Список типов документов для фильтрации
        context['document_types'] = DocumentTemplate.DOCUMENT_TYPES

        # Значения для выбранных фильтров
        context['selected_employee'] = self.request.GET.get('employee', '')
        context['selected_type'] = self.request.GET.get('type', 'all')

        return context


class GeneratedDocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для просмотра деталей сгенерированного документа
    """
    model = GeneratedDocument
    template_name = 'directory/documents/document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        """
        Подготовка контекста для шаблона
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Просмотр документа')
        return context


def document_download(request, pk):
    """
    Функция для скачивания сгенерированного документа
    """
    document = get_object_or_404(GeneratedDocument, pk=pk)

    # Проверка доступа к документу
    # Если нужно ограничить доступ, например, только создателю или администратору
    # if request.user != document.created_by and not request.user.is_staff:
    #     raise PermissionDenied

    # Получаем файл
    file_handle = document.document_file.open()

    # Формируем имя файла для скачивания
    filename = document.document_file.name.split('/')[-1]

    # Возвращаем файл в ответе
    response = FileResponse(
        file_handle,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response