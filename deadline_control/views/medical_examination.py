from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import datetime

from deadline_control.models.medical_examination import MedicalExaminationType, HarmfulFactor, MedicalSettings
from deadline_control.models.medical_norm import (
    MedicalExaminationNorm,
    PositionMedicalFactor,
    EmployeeMedicalExamination
)
from directory.models.position import Position
from directory.models.employee import Employee
from deadline_control.forms.medical_examination import (
    MedicalExaminationTypeForm,
    HarmfulFactorForm,
    MedicalExaminationNormForm,
    PositionMedicalFactorForm,
    EmployeeMedicalExaminationForm,
    MedicalSettingsForm,
    MedicalNormImportForm,
    MedicalNormExportForm,
    MedicalNormSearchForm,
    EmployeeMedicalExaminationSearchForm
)
from directory.utils.medical_examination import (
    import_medical_norms_from_file,
    export_medical_norms,
    find_medical_norms_for_position,
    get_employee_medical_examination_status,
    update_medical_examination_statuses
)


# Виды медосмотров
class MedicalExaminationTypeListView(LoginRequiredMixin, ListView):
    """
    Отображение списка видов медицинских осмотров
    """
    model = MedicalExaminationType
    template_name = 'directory/medical_exams/exam_types/list.html'
    context_object_name = 'exam_types'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class MedicalExaminationTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Создание нового вида медицинского осмотра
    """
    model = MedicalExaminationType
    form_class = MedicalExaminationTypeForm
    template_name = 'directory/medical_exams/exam_types/form.html'
    success_url = reverse_lazy('directory:medical_examination_types')
    permission_required = 'directory.add_medicalexaminationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление вида медосмотра'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Вид медосмотра "{form.instance.name}" успешно создан')
        return super().form_valid(form)


class MedicalExaminationTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Редактирование вида медицинского осмотра
    """
    model = MedicalExaminationType
    form_class = MedicalExaminationTypeForm
    template_name = 'directory/medical_exams/exam_types/form.html'
    success_url = reverse_lazy('directory:medical_examination_types')
    permission_required = 'directory.change_medicalexaminationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Вид медосмотра "{form.instance.name}" успешно отредактирован')
        return super().form_valid(form)


class MedicalExaminationTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Удаление вида медицинского осмотра
    """
    model = MedicalExaminationType
    template_name = 'directory/medical_exams/exam_types/confirm_delete.html'
    success_url = reverse_lazy('directory:medical_examination_types')
    permission_required = 'directory.delete_medicalexaminationtype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем наличие связанных объектов
        context['has_related_objects'] = self.object.harmful_factors.exists()
        return context

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect('directory:medical_examination_types')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        success_url = self.get_success_url()
        try:
            self.object.delete()
            messages.success(request, f'Вид медосмотра "{name}" успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
        return redirect(success_url)


# Вредные факторы
class HarmfulFactorListView(LoginRequiredMixin, ListView):
    """
    Отображение списка вредных факторов
    """
    model = HarmfulFactor
    template_name = 'directory/medical_exams/harmful_factors/list.html'
    context_object_name = 'harmful_factors'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('examination_type')

        search_query = self.request.GET.get('search', '')
        exam_type_id = self.request.GET.get('exam_type', '')

        if search_query:
            queryset = queryset.filter(
                Q(short_name__icontains=search_query) |
                Q(full_name__icontains=search_query)
            )

        if exam_type_id and exam_type_id.isdigit():
            queryset = queryset.filter(examination_type_id=exam_type_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['exam_type_id'] = self.request.GET.get('exam_type', '')
        context['exam_types'] = MedicalExaminationType.objects.all()
        return context


class HarmfulFactorDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр вредного фактора
    """
    model = HarmfulFactor
    template_name = 'directory/medical_exams/harmful_factors/detail.html'
    context_object_name = 'harmful_factor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем связанные нормы
        context['norms'] = MedicalExaminationNorm.objects.filter(
            harmful_factor=self.object
        ).order_by('position_name')
        return context


class HarmfulFactorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Создание нового вредного фактора
    """
    model = HarmfulFactor
    form_class = HarmfulFactorForm
    template_name = 'directory/medical_exams/harmful_factors/form.html'
    success_url = reverse_lazy('directory:harmful_factors')
    permission_required = 'directory.add_harmfulfactor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление вредного фактора'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Вредный фактор "{form.instance.short_name}" успешно создан')
        return super().form_valid(form)


class HarmfulFactorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Редактирование вредного фактора
    """
    model = HarmfulFactor
    form_class = HarmfulFactorForm
    template_name = 'directory/medical_exams/harmful_factors/form.html'
    success_url = reverse_lazy('directory:harmful_factors')
    permission_required = 'directory.change_harmfulfactor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.short_name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Вредный фактор "{form.instance.short_name}" успешно отредактирован')
        return super().form_valid(form)

    def get_success_url(self):
        if 'continue' in self.request.POST:
            return reverse('directory:harmful_factor_detail', kwargs={'pk': self.object.pk})
        return super().get_success_url()


class HarmfulFactorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Удаление вредного фактора
    """
    model = HarmfulFactor
    template_name = 'directory/medical_exams/harmful_factors/confirm_delete.html'
    success_url = reverse_lazy('directory:harmful_factors')
    permission_required = 'directory.delete_harmfulfactor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем наличие связанных объектов
        context['related_norms_count'] = MedicalExaminationNorm.objects.filter(harmful_factor=self.object).count()
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.short_name
        success_url = self.get_success_url()
        try:
            self.object.delete()
            messages.success(request, f'Вредный фактор "{name}" успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
        return redirect(success_url)


# Нормы медицинских осмотров
class MedicalNormListView(LoginRequiredMixin, ListView):
    """
    Отображение списка норм медицинских осмотров
    """
    model = MedicalExaminationNorm
    template_name = 'directory/medical_exams/medical_norms/list.html'
    context_object_name = 'norms'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset().select_related('harmful_factor', 'harmful_factor__examination_type')

        # Получаем параметры поиска
        form = MedicalNormSearchForm(self.request.GET)
        if form.is_valid():
            position_name = form.cleaned_data.get('position_name')
            examination_type = form.cleaned_data.get('examination_type')
            harmful_factor = form.cleaned_data.get('harmful_factor')

            if position_name:
                queryset = queryset.filter(position_name__icontains=position_name)

            if examination_type:
                queryset = queryset.filter(harmful_factor__examination_type=examination_type)

            if harmful_factor:
                queryset = queryset.filter(
                    Q(harmful_factor__short_name__icontains=harmful_factor) |
                    Q(harmful_factor__full_name__icontains=harmful_factor)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = MedicalNormSearchForm(self.request.GET)
        context['import_form'] = MedicalNormImportForm()
        context['export_form'] = MedicalNormExportForm()
        return context


class MedicalNormCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Создание новой нормы медицинского осмотра
    """
    model = MedicalExaminationNorm
    form_class = MedicalExaminationNormForm
    template_name = 'directory/medical_exams/medical_norms/form.html'
    success_url = reverse_lazy('directory:medical_norms')
    permission_required = 'directory.add_medicalexaminationnorm'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление нормы медосмотра'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Норма медосмотра для должности "{form.instance.position_name}" успешно создана'
        )
        return super().form_valid(form)


class MedicalNormUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Редактирование нормы медицинского осмотра
    """
    model = MedicalExaminationNorm
    form_class = MedicalExaminationNormForm
    template_name = 'directory/medical_exams/medical_norms/form.html'
    success_url = reverse_lazy('directory:medical_norms')
    permission_required = 'directory.change_medicalexaminationnorm'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование нормы для должности "{self.object.position_name}"'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Норма медосмотра для должности "{form.instance.position_name}" успешно обновлена'
        )
        return super().form_valid(form)


class MedicalNormDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Удаление нормы медицинского осмотра
    """
    model = MedicalExaminationNorm
    template_name = 'directory/medical_exams/medical_norms/confirm_delete.html'
    success_url = reverse_lazy('directory:medical_norms')
    permission_required = 'directory.delete_medicalexaminationnorm'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        position_name = self.object.position_name
        factor = self.object.harmful_factor.short_name
        success_url = self.get_success_url()

        try:
            self.object.delete()
            messages.success(
                request,
                f'Норма медосмотра для должности "{position_name}" (фактор: {factor}) успешно удалена'
            )
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')

        return redirect(success_url)


class MedicalNormImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Импорт норм медицинских осмотров из файла
    """
    form_class = MedicalNormImportForm
    template_name = 'directory/medical_exams/medical_norms/import.html'
    success_url = reverse_lazy('directory:medical_norms')
    permission_required = 'directory.add_medicalexaminationnorm'

    def form_valid(self, form):
        file = self.request.FILES['file']
        skip_first_row = form.cleaned_data['skip_first_row']
        update_existing = form.cleaned_data['update_existing']

        result = import_medical_norms_from_file(file, skip_first_row, update_existing)

        if result['success']:
            if result['errors']:
                for error in result['errors'][:10]:  # Показываем первые 10 ошибок
                    messages.warning(self.request, error)

                if len(result['errors']) > 10:
                    messages.warning(self.request, f'... и еще {len(result["errors"]) - 10} ошибок')

            messages.success(
                self.request,
                f'Импорт завершен. Обработано строк: {result["total_rows"]}, '
                f'добавлено: {result["imported"]}, обновлено: {result["updated"]}'
            )
        else:
            messages.error(self.request, result['message'])

        return super().form_valid(form)


class MedicalNormExportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Экспорт норм медицинских осмотров в файл
    """
    form_class = MedicalNormExportForm
    template_name = 'directory/medical_exams/medical_norms/export.html'
    success_url = reverse_lazy('directory:medical_norms')
    permission_required = 'directory.view_medicalexaminationnorm'

    def form_valid(self, form):
        format_type = form.cleaned_data['format']
        include_headers = form.cleaned_data['include_headers']

        response = export_medical_norms(format_type, include_headers)
        return response


# Настройки медосмотров
class MedicalSettingsView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Представление для настройки параметров модуля медосмотров
    """
    model = MedicalSettings
    form_class = MedicalSettingsForm
    template_name = 'directory/medical_exams/settings/form.html'
    success_url = reverse_lazy('directory:medical_settings')
    permission_required = 'directory.change_medicalsettings'

    def get_object(self, queryset=None):
        # Получаем или создаем настройки
        settings, created = MedicalSettings.objects.get_or_create(pk=1)
        return settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Настройки медосмотров'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Настройки медосмотров успешно обновлены')
        return super().form_valid(form)


# Медицинские осмотры сотрудников
class EmployeeMedicalExaminationListView(LoginRequiredMixin, ListView):
    """
    Отображение списка медицинских осмотров сотрудников
    """
    model = EmployeeMedicalExamination
    template_name = 'directory/medical_exams/employee_exams/list.html'
    context_object_name = 'exams'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'employee', 'examination_type', 'harmful_factor', 'employee__position'
        )

        # Получаем параметры поиска
        form = EmployeeMedicalExaminationSearchForm(self.request.GET)
        if form.is_valid():
            employee = form.cleaned_data.get('employee')
            examination_type = form.cleaned_data.get('examination_type')
            status = form.cleaned_data.get('status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')

            if employee:
                queryset = queryset.filter(
                    Q(employee__full_name_nominative__icontains=employee)
                )

            if examination_type:
                queryset = queryset.filter(examination_type=examination_type)

            if status:
                queryset = queryset.filter(status=status)

            if date_from:
                queryset = queryset.filter(date_completed__gte=date_from)

            if date_to:
                queryset = queryset.filter(date_completed__lte=date_to)

        # Обновляем статусы просроченных медосмотров
        update_medical_examination_statuses()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = EmployeeMedicalExaminationSearchForm(self.request.GET)
        return context


class EmployeeMedicalExaminationDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр медицинского осмотра сотрудника
    """
    model = EmployeeMedicalExamination
    template_name = 'directory/medical_exams/employee_exams/detail.html'
    context_object_name = 'exam'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем другие медосмотры этого сотрудника
        context['other_exams'] = EmployeeMedicalExamination.objects.filter(
            employee=self.object.employee
        ).exclude(
            id=self.object.id
        ).order_by('-date_completed')[:5]

        # Получаем статус медосмотров сотрудника
        context['status_info'] = get_employee_medical_examination_status(self.object.employee)

        return context


class EmployeeMedicalExaminationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Создание записи о медицинском осмотре сотрудника
    """
    model = EmployeeMedicalExamination
    form_class = EmployeeMedicalExaminationForm
    template_name = 'directory/medical_exams/employee_exams/form.html'
    success_url = reverse_lazy('directory:employee_exams')
    permission_required = 'directory.add_employeemedicalexamination'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление медосмотра сотруднику'

        # Если указан сотрудник, предзаполняем форму и показываем его статус
        employee_id = self.request.GET.get('employee_id')
        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id)
                context['employee'] = employee
                context['status_info'] = get_employee_medical_examination_status(employee)
            except Employee.DoesNotExist:
                pass

        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Медосмотр сотрудника {form.instance.employee} успешно добавлен'
        )
        return response

    def get_success_url(self):
        if 'continue' in self.request.POST:
            return reverse('directory:employee_exam_detail', kwargs={'pk': self.object.pk})
        elif 'add_another' in self.request.POST:
            return reverse('directory:employee_exam_create')
        return super().get_success_url()


class EmployeeMedicalExaminationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Редактирование медицинского осмотра сотрудника
    """
    model = EmployeeMedicalExamination
    form_class = EmployeeMedicalExaminationForm
    template_name = 'directory/medical_exams/employee_exams/form.html'
    success_url = reverse_lazy('directory:employee_exams')
    permission_required = 'directory.change_employeemedicalexamination'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование медосмотра {self.object.employee}'
        context['employee'] = self.object.employee
        context['status_info'] = get_employee_medical_examination_status(self.object.employee)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Медосмотр сотрудника {form.instance.employee} успешно обновлен'
        )
        return response

    def get_success_url(self):
        if 'continue' in self.request.POST:
            return reverse('directory:employee_exam_detail', kwargs={'pk': self.object.pk})
        return super().get_success_url()


class EmployeeMedicalExaminationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Удаление записи о медицинском осмотре сотрудника
    """
    model = EmployeeMedicalExamination
    template_name = 'directory/medical_exams/employee_exams/confirm_delete.html'
    success_url = reverse_lazy('directory:employee_exams')
    permission_required = 'directory.delete_employeemedicalexamination'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        employee = self.object.employee
        exam_type = self.object.examination_type
        date = self.object.date_completed

        success_url = self.get_success_url()

        try:
            self.object.delete()
            messages.success(
                request,
                f'Запись о медосмотре сотрудника {employee} ({exam_type}, {date}) успешно удалена'
            )
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')

        return redirect(success_url)


class EmployeeMedicalExaminationTabView(LoginRequiredMixin, TemplateView):
    """
    Вкладка медицинских осмотров на странице сотрудника
    """
    template_name = 'directory/medical_exams/employee_exams/employee_exams_tab.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = kwargs.get('employee_id')
        employee = get_object_or_404(Employee, pk=employee_id)

        context['employee'] = employee
        context['exams'] = EmployeeMedicalExamination.objects.filter(
            employee=employee
        ).select_related('examination_type', 'harmful_factor').order_by('-date_completed')

        # Получаем статус медосмотров сотрудника
        context['status_info'] = get_employee_medical_examination_status(employee)

        return context


# API для работы с медосмотрами
def api_employee_medical_status(request, employee_id):
    """
    API для получения статуса медосмотров сотрудника
    """
    try:
        employee = Employee.objects.get(pk=employee_id)
        status_info = get_employee_medical_examination_status(employee)

        result = {
            'status': status_info['status'],
            'message': status_info['message'],
            'employee_id': employee.id,
            'employee_name': employee.full_name_nominative,
        }

        return JsonResponse(result)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Сотрудник не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_position_medical_norms(request, position_id):
    """
    API для получения норм медосмотров для должности
    """
    try:
        position = Position.objects.get(pk=position_id)
        norms = find_medical_norms_for_position(position)

        result = {
            'position_id': position.id,
            'position_name': position.position_name,
            'norms': [
                {
                    'factor_id': norm['factor'].id,
                    'factor_code': norm['factor'].short_name,
                    'factor_name': norm['factor'].full_name,
                    'examination_type_id': norm['examination_type'].id,
                    'examination_type_name': norm['examination_type'].name,
                    'periodicity': norm['periodicity'],
                    'is_override': norm['is_override'],
                    'is_disabled': norm['is_disabled'],
                }
                for norm in norms
            ]
        }

        return JsonResponse(result)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)