"""
📄 Представления для работы с документами

Этот модуль содержит представления для выбора, настройки, предпросмотра
и генерации различных документов.
"""
import json
import datetime
from django.views.generic import FormView, DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.utils import timezone

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.forms.document_forms import (
    DocumentSelectionForm, InternshipOrderForm, AdmissionOrderForm, DocumentPreviewForm
)
from directory.utils.docx_generator import (
    prepare_employee_context, generate_docx_from_template,
    generate_internship_order, generate_admission_order
)
from directory.utils.declension import (
    decline_full_name, decline_phrase, get_initials_from_name
)


class DocumentSelectionView(LoginRequiredMixin, FormView):
    """
    Представление для выбора типа документа для генерации
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
        context['title'] = _('Выбор типа документа')
        return context

    def form_valid(self, form):
        employee_id = form.cleaned_data['employee_id']
        document_type = form.cleaned_data['document_type']

        # Перенаправляем на соответствующую форму в зависимости от типа документа
        if document_type == 'internship_order':
            return redirect('directory:documents:internship_order_form', employee_id=employee_id)
        elif document_type == 'admission_order':
            return redirect('directory:documents:admission_order_form', employee_id=employee_id)
        elif document_type == 'knowledge_protocol':
            return redirect('directory:documents:knowledge_protocol_form', employee_id=employee_id)
        elif document_type == 'doc_familiarization':
            return redirect('directory:documents:doc_familiarization_form', employee_id=employee_id)

        # Если тип документа неизвестен, возвращаемся на форму выбора
        messages.error(self.request, _('Неизвестный тип документа'))
        return redirect('directory:documents:document_selection', employee_id=employee_id)


class InternshipOrderFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о стажировке
    """
    template_name = 'directory/documents/internship_order_form.html'
    form_class = InternshipOrderForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

        # Подготавливаем начальные данные для формы на основе данных сотрудника
        context = prepare_employee_context(employee)

        # Получаем информацию о руководителе стажировки
        internship_leader = None
        if employee.department:
            internship_leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()

        # Заполняем начальные данные формы
        initial.update({
            'organization_name': context['organization_name'],
            'fio_dative': context['fio_dative'],
            'position_dative': context['position_dative'],
            'department': context['department'],
            'subdivision': context['subdivision'],
            'internship_duration': context.get('internship_duration', '2'),
            'order_date': timezone.now().date(),
            'location': context.get('location', 'г. Минск'),
            'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
        })

        # Добавляем информацию о руководителе стажировки, если он найден
        if internship_leader:
            initial.update({
                'head_of_internship_position': internship_leader.position.position_name if internship_leader.position else "",
                'head_of_internship_name': internship_leader.full_name_nominative,
                'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            })

        # Добавляем информацию о директоре (в данном случае берем из организации)
        if employee.organization:
            initial['director_name'] = "И.И. Коржов"  # Здесь можно получать из данных организации
            initial['director_position'] = "Директор"

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        context['employee'] = employee
        context['title'] = _('Распоряжение о стажировке')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.get_employee()
        return kwargs

    def form_valid(self, form):
        employee = self.get_employee()

        # Если нажата кнопка предпросмотра
        if 'preview' in self.request.POST:
            # Собираем данные для предпросмотра
            document_data = form.cleaned_data
            document_data['employee_id'] = employee.id

            # Передаем данные форме предпросмотра
            preview_form = DocumentPreviewForm(initial={
                'document_data': json.dumps(document_data, default=str),
                'document_type': 'internship_order',
                'employee_id': employee.id
            })

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'internship_order',
                    'employee': employee,
                    'title': _('Предпросмотр распоряжения о стажировке')
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
            custom_context = form.cleaned_data
            generated_doc = generate_internship_order(
                employee,
                self.request.user,
                custom_context
            )

            if generated_doc:
                messages.success(
                    self.request,
                    _('Распоряжение о стажировке успешно сгенерировано')
                )
                return redirect('directory:documents:document_detail', pk=generated_doc.id)
            else:
                messages.error(
                    self.request,
                    _('Ошибка при генерации документа')
                )
                return self.form_invalid(form)

        return super().form_valid(form)


class AdmissionOrderFormView(LoginRequiredMixin, FormView):
    """
    Представление для формы распоряжения о допуске к самостоятельной работе
    """
    template_name = 'directory/documents/admission_order_form.html'
    form_class = AdmissionOrderForm

    def get_employee(self):
        employee_id = self.kwargs.get('employee_id')
        return get_object_or_404(Employee, id=employee_id)

    def get_initial(self):
        initial = super().get_initial()
        employee = self.get_employee()

        # Подготавливаем начальные данные для формы на основе данных сотрудника
        context = prepare_employee_context(employee)

        # Получаем информацию о руководителе (тот же, что и для стажировки)
        internship_leader = None
        if employee.department:
            internship_leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()

        # Заполняем начальные данные формы
        initial.update({
            'organization_name': context['organization_name'],
            'fio_nominative': context['fio_nominative'],
            'position_nominative': context['position_nominative'],
            'department': context['department'],
            'subdivision': context['subdivision'],
            'order_date': timezone.now().date(),
            'location': context.get('location', 'г. Минск'),
            'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
        })

        # Добавляем информацию о руководителе, если он найден
        if internship_leader:
            initial.update({
                'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            })

        # Добавляем информацию о директоре (в данном случае берем из организации)
        if employee.organization:
            initial['director_name'] = "И.И. Коржов"  # Здесь можно получать из данных организации
            initial['director_position'] = "Директор"

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_employee()
        context['employee'] = employee
        context['title'] = _('Распоряжение о допуске к самостоятельной работе')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.get_employee()
        return kwargs

    def form_valid(self, form):
        employee = self.get_employee()

        # Если нажата кнопка предпросмотра
        if 'preview' in self.request.POST:
            # Собираем данные для предпросмотра
            document_data = form.cleaned_data
            document_data['employee_id'] = employee.id

            # Передаем данные форме предпросмотра
            preview_form = DocumentPreviewForm(initial={
                'document_data': json.dumps(document_data, default=str),
                'document_type': 'admission_order',
                'employee_id': employee.id
            })

            # Рендерим страницу предпросмотра
            return render(
                self.request,
                'directory/documents/document_preview.html',
                {
                    'form': preview_form,
                    'document_data': document_data,
                    'document_type': 'admission_order',
                    'employee': employee,
                    'title': _('Предпросмотр распоряжения о допуске к самостоятельной работе')
                }
            )

        # Если нажата кнопка генерации документа
        elif 'generate' in self.request.POST:
            # Генерируем документ
            custom_context = form.cleaned_data
            generated_doc = generate_admission_order(
                employee,
                self.request.user,
                custom_context
            )

            if generated_doc:
                messages.success(
                    self.request,
                    _('Распоряжение о допуске к самостоятельной работе успешно сгенерировано')
                )
                return redirect('directory:documents:document_detail', pk=generated_doc.id)
            else:
                messages.error(
                    self.request,
                    _('Ошибка при генерации документа')
                )
                return self.form_invalid(form)

        return super().form_valid(form)


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

        if generated_doc:
            messages.success(self.request, success_message)
            return redirect('directory:documents:document_detail', pk=generated_doc.id)
        else:
            messages.error(self.request, _('Ошибка при генерации документа'))
            return self.form_invalid(form)


class GeneratedDocumentListView(LoginRequiredMixin, ListView):
    """
    Представление для списка сгенерированных документов
    """
    model = GeneratedDocument
    template_name = 'directory/documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()

        # Применяем фильтры, если они есть
        employee_id = self.request.GET.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        doc_type = self.request.GET.get('type')
        if doc_type and doc_type != 'all':
            qs = qs.filter(template__document_type=doc_type)

        # Сортировка по дате создания (сначала новые)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Сгенерированные документы')

        # Добавляем фильтры
        context['employees'] = Employee.objects.all().order_by('full_name_nominative')
        context['document_types'] = DocumentTemplate.DOCUMENT_TYPES

        # Текущие значения фильтров
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
        context = super().get_context_data(**kwargs)
        context['title'] = _('Просмотр документа')
        return context


def document_download(request, pk):
    """
    Функция для скачивания сгенерированного документа
    """
    document = get_object_or_404(GeneratedDocument, pk=pk)

    # Открываем файл для чтения
    file_path = document.document_file.path

    # Возвращаем файл для скачивания
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{document.document_file.name.split("/")[-1]}"'
    return response


@require_POST
def update_preview_data(request):
    """
    Обработчик AJAX-запроса для обновления данных предпросмотра
    """
    try:
        data = json.loads(request.body)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)