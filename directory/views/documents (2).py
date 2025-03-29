# directory/views/documents.py
"""
📄 Представления для работы с документами

Этот модуль содержит представления для выбора, настройки, предпросмотра
и генерации различных типов документов.
"""
import json
import datetime
from django.views.generic import FormView, DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.forms.document_forms import (
    DocumentSelectionForm, InternshipOrderForm, AdmissionOrderForm, DocumentPreviewForm
)
from directory.utils.docx_generator import (
    prepare_employee_context, generate_docx_from_template,
    generate_internship_order, generate_admission_order,
    generate_knowledge_protocol, generate_doc_familiarization
)
from directory.utils.declension import (
    decline_full_name, decline_phrase, get_initials_from_name
)


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
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get('employee_id')
        if employee_id:
            context['employee'] = get_object_or_404(Employee, id=employee_id)
        context['title'] = _('Выбор типов документов')
        return context

    def form_valid(self, form):
        try:
            employee_id = form.cleaned_data['employee_id']
            document_types = form.cleaned_data.get('document_types', [])
            
            # Проверяем, пришли ли типы документов
            if not document_types:
                # Проверяем альтернативные имена полей, которые могут прийти из формы
                for field_name in ['document_type', 'document-types']:
                    if field_name in form.cleaned_data:
                        document_types = form.cleaned_data[field_name]
                        if not isinstance(document_types, list):
                            document_types = [document_types]
                        break
                
                # Если все еще нет типов документов, смотрим в request.POST
                if not document_types:
                    document_types = self.request.POST.getlist('document_types')
            
            # Если все еще нет типов документов, выдаем ошибку
            if not document_types:
                messages.error(self.request, _("Необходимо выбрать хотя бы один тип документа"))
                return self.form_invalid(form)
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            # Подготавливаем базовый контекст на основе данных сотрудника
            base_context = prepare_employee_context(employee)
            
            # Создаем предпросмотры для всех выбранных типов документов
            preview_data = []
            
            for doc_type in document_types:
                # Создаем контекст для каждого типа документа
                context = self._prepare_document_context(doc_type, employee, base_context)
                
                # Добавляем информацию о типе документа и данные для предпросмотра
                preview_data.append({
                    'document_type': doc_type,
                    'document_data': context,
                    'employee_id': employee_id
                })
            
            # Сохраняем данные предпросмотра в сессию для использования на странице предпросмотра
            self.request.session['preview_data'] = json.dumps(preview_data, default=str)
            
            # Перенаправляем на страницу предпросмотра
            return HttpResponseRedirect(reverse('directory:documents:documents_preview'))
        except Exception as e:
            messages.error(self.request, f"Ошибка при обработке формы: {str(e)}")
            return self.form_invalid(form)

    def _prepare_document_context(self, document_type, employee, base_context):
        """
        Подготавливает контекст для определенного типа документа
        """
        context = base_context.copy()
        missing_data = []
        
        # Добавляем дополнительные данные в зависимости от типа документа
        if document_type == 'internship_order':
            # Данные для распоряжения о стажировке
            internship_data = {
                'order_number': '',  # Номер распоряжения (пользователь должен ввести)
            }
            
            # Период стажировки
            if hasattr(employee.position, 'internship_period_days') and employee.position.internship_period_days:
                internship_data['internship_duration'] = employee.position.internship_period_days
            else:
                internship_data['internship_duration'] = 2
                missing_data.append('Период стажировки не указан в должности')
            
            # Информация о руководителе стажировки
            leader_position, position_success = self._get_internship_leader_position(employee)
            if not position_success:
                missing_data.append('Не найден руководитель стажировки')
            
            leader_name, name_success = self._get_internship_leader_name(employee)
            if not name_success:
                missing_data.append('Не найдено ФИО руководителя стажировки')
            
            leader_initials, initials_success = self._get_internship_leader_initials(employee)
            if not initials_success:
                missing_data.append('Не найдены инициалы руководителя стажировки')
            
            internship_data.update({
                'head_of_internship_position': leader_position,
                'head_of_internship_name': leader_name,
                'head_of_internship_name_initials': leader_initials,
            })
            
            # Информация о директоре (должна храниться в организации)
            director_info, director_success = self._get_director_info(employee.organization)
            if not director_success:
                missing_data.append('Не найдена информация о директоре')
            
            internship_data.update({
                'director_position': director_info['position'],
                'director_name': director_info['name'],
            })
            
            context.update(internship_data)
            
        elif document_type == 'admission_order':
            # Данные для распоряжения о допуске к самостоятельной работе
            admission_data = {
                'order_number': '',  # Номер распоряжения (пользователь должен ввести)
            }
            
            # Информация о директоре
            director_info, director_success = self._get_director_info(employee.organization)
            if not director_success:
                missing_data.append('Не найдена информация о директоре')
            
            admission_data.update({
                'director_position': director_info['position'],
                'director_name': director_info['name'],
            })
            
            # Используем того же руководителя, что и для стажировки
            leader_initials, initials_success = self._get_internship_leader_initials(employee)
            if not initials_success:
                missing_data.append('Не найдены инициалы руководителя')
            
            admission_data['head_of_internship_name_initials'] = leader_initials
            
            context.update(admission_data)
            
        elif document_type == 'knowledge_protocol':
            # Данные для протокола проверки знаний
            protocol_data = {
                'protocol_number': '',  # Номер протокола (пользователь должен ввести)
                'knowledge_result': 'удовлетворительные',
            }
            
            # Члены комиссии
            commission_members, commission_success = self._get_commission_members(employee)
            if not commission_success:
                missing_data.append('Не найдены члены комиссии')
            
            protocol_data['commission_members'] = commission_members
            
            # Инструкции по охране труда
            safety_instructions, instructions_success = self._get_safety_instructions(employee)
            if not instructions_success:
                missing_data.append('Не найдены инструкции по охране труда')
            
            protocol_data['safety_instructions'] = safety_instructions
            
            context.update(protocol_data)
            
        elif document_type == 'doc_familiarization':
            # Данные для листа ознакомления с документами
            familiarization_data = {
                'familiarization_date': base_context.get('order_date', ''),
            }
            
            # Документы для ознакомления
            documents_list, documents_success = self._get_employee_documents(employee)
            if not documents_success:
                missing_data.append('Не найдены документы для ознакомления')
            
            familiarization_data['documents_list'] = documents_list
            
            context.update(familiarization_data)
        
        # Добавляем информацию о недостающих данных в контекст
        context['missing_data'] = missing_data
        context['has_missing_data'] = len(missing_data) > 0
        
        return context

    def _get_internship_leader_position(self, employee):
        """
        Получает должность руководителя стажировки для сотрудника
        
        Returns:
            tuple: (position_name, success)
        """
        # Если есть отдел, ищем руководителя стажировки в отделе
        if employee.department:
            leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()
            if leader and leader.position:
                return leader.position.position_name, True
        
        # Не найдено
        return "Необходимо указать должность руководителя стажировки", False

    def _get_internship_leader_name(self, employee):
        """
        Получает ФИО руководителя стажировки для сотрудника
        
        Returns:
            tuple: (name, success)
        """
        # Если есть отдел, ищем руководителя стажировки в отделе
        if employee.department:
            leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()
            if leader:
                return leader.full_name_nominative, True
        
        # Не найдено
        return "Необходимо указать ФИО руководителя стажировки", False

    def _get_internship_leader_initials(self, employee):
        """
        Получает инициалы руководителя стажировки для сотрудника
        
        Returns:
            tuple: (initials, success)
        """
        # Если есть отдел, ищем руководителя стажировки в отделе
        if employee.department:
            leader = employee.department.employees.filter(
                position__can_be_internship_leader=True
            ).first()
            if leader:
                return get_initials_from_name(leader.full_name_nominative), True
        
        # Не найдено
        return "Необходимо указать инициалы руководителя стажировки", False

    def _get_director_info(self, organization):
        """
        Получает информацию о директоре организации
        
        Returns:
            tuple: ({'position': position, 'name': name}, success)
        """
        # Здесь должна быть реальная логика получения информации о директоре из организации
        # В реальной системе эта информация должна храниться в модели организации
        
        # Проверка наличия информации о директоре в организации
        if organization and hasattr(organization, 'director_name') and organization.director_name:
            return {
                'position': getattr(organization, 'director_position', 'Директор'),
                'name': organization.director_name
            }, True
        
        # Не найдено
        return {
            'position': "Директор",
            'name': "Необходимо указать ФИО директора"
        }, False

    def _get_commission_members(self, employee):
        """
        Получает список членов комиссии для протокола проверки знаний
        
        Returns:
            tuple: (members_list, success)
        """
        # Проверяем наличие информации о комиссии
        if hasattr(employee.organization, 'commission_members'):
            commission = getattr(employee.organization, 'commission_members', None)
            if commission and len(commission) > 0:
                return commission, True
        
        # Не найдено - возвращаем шаблон, который пользователь должен заполнить
        return [
            {"role": "Председатель комиссии", "name": "Необходимо указать"},
            {"role": "Член комиссии", "name": "Необходимо указать"},
            {"role": "Член комиссии", "name": "Необходимо указать"},
        ], False

    def _get_safety_instructions(self, employee):
        """
        Получает список инструкций по охране труда для сотрудника
        
        Returns:
            tuple: (instructions_list, success)
        """
        # Если у сотрудника есть должность с указанными инструкциями
        if employee.position and hasattr(employee.position, 'safety_instructions_numbers'):
            instructions = employee.position.safety_instructions_numbers
            if instructions:
                # Разбиваем строку с номерами инструкций на список
                instructions_list = [instr.strip() for instr in instructions.split(',')]
                return instructions_list, True
        
        # Не найдено
        return ["Необходимо указать инструкции"], False

    def _get_employee_documents(self, employee):
        """
        Получает список документов, с которыми должен ознакомиться сотрудник
        
        Returns:
            tuple: (documents_list, success)
        """
        # Если у сотрудника есть должность с привязанными документами
        if employee.position and hasattr(employee.position, 'documents'):
            documents = employee.position.documents.all()
            if documents.exists():
                documents_list = [doc.name for doc in documents]
                return documents_list, True
        
        # Не найдено
        return ["Необходимо указать список документов"], False


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
                generated_doc = generate_admission_order(employee,
               request.user,
               document_data
           )
           elif doc_type == 'knowledge_protocol':
               generated_doc = generate_knowledge_protocol(
                   employee,
                   request.user,
                   document_data
               )
           elif doc_type == 'doc_familiarization':
               generated_doc = generate_doc_familiarization(
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