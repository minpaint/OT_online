import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Prefetch
from django import forms  # Добавлен импорт forms

from directory.models import EmployeeHiring, Organization, Employee
from directory.forms.hiring import EmployeeHiringRecordForm, DocumentAttachmentForm
from directory.utils.hiring_utils import create_hiring_from_employee, attach_document_to_hiring

logger = logging.getLogger(__name__)


class HiringTreeView(LoginRequiredMixin, ListView):
    """
    Древовидное представление записей о приеме на работу
    по организационной структуре
    """
    model = EmployeeHiring
    template_name = 'directory/hiring/tree_view.html'
    context_object_name = 'hiring_records'

    def get_queryset(self):
        # Фильтрация по активности
        is_active = self.request.GET.get('is_active')
        queryset = EmployeeHiring.objects.all()

        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Фильтрация по типу приема
        hiring_type = self.request.GET.get('hiring_type')
        if hiring_type:
            queryset = queryset.filter(hiring_type=hiring_type)

        # Поиск по ФИО
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__full_name_nominative__icontains=search) |
                Q(position__position_name__icontains=search)
            )

        # Ограничение по организациям пользователя
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        return queryset.select_related(
            'employee', 'organization', 'subdivision', 'department', 'position'
        ).prefetch_related('documents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Приемы на работу')

        # Получаем доступные организации
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
        else:
            allowed_orgs = Organization.objects.all()

        # Создаем древовидную структуру данных
        tree_data = []

        for org in allowed_orgs:
            org_hirings = self.get_queryset().filter(
                organization=org,
                subdivision__isnull=True,
                department__isnull=True
            )

            if not org_hirings.exists() and not org.subdivisions.exists():
                continue  # Пропускаем пустые организации

            org_data = {
                'id': org.id,
                'name': org.short_name_ru or org.full_name_ru,
                'hirings': list(org_hirings),
                'subdivisions': []
            }

            # Получаем подразделения
            for subdivision in org.subdivisions.all():
                sub_hirings = self.get_queryset().filter(
                    organization=org,
                    subdivision=subdivision,
                    department__isnull=True
                )

                if not sub_hirings.exists() and not subdivision.departments.exists():
                    continue  # Пропускаем пустые подразделения

                sub_data = {
                    'id': subdivision.id,
                    'name': subdivision.name,
                    'hirings': list(sub_hirings),
                    'departments': []
                }

                # Получаем отделы
                for department in subdivision.departments.all():
                    dept_hirings = self.get_queryset().filter(
                        organization=org,
                        subdivision=subdivision,
                        department=department
                    )

                    if not dept_hirings.exists():
                        continue  # Пропускаем пустые отделы

                    dept_data = {
                        'id': department.id,
                        'name': department.name,
                        'hirings': list(dept_hirings)
                    }

                    sub_data['departments'].append(dept_data)

                org_data['subdivisions'].append(sub_data)

            tree_data.append(org_data)

        context['tree_data'] = tree_data
        context['hiring_types'] = dict(EmployeeHiring.HIRING_TYPE_CHOICES)

        # Параметры фильтрации
        context['current_hiring_type'] = self.request.GET.get('hiring_type', '')
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['search_query'] = self.request.GET.get('search', '')

        return context


class HiringListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка записей о приеме на работу
    """
    model = EmployeeHiring
    template_name = 'directory/hiring/list.html'
    context_object_name = 'hiring_records'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Применяем те же фильтры, что и в TreeView
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        hiring_type = self.request.GET.get('hiring_type')
        if hiring_type:
            queryset = queryset.filter(hiring_type=hiring_type)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__full_name_nominative__icontains=search) |
                Q(position__position_name__icontains=search)
            )

        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        return queryset.select_related(
            'employee', 'organization', 'subdivision', 'department', 'position'
        ).prefetch_related('documents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Приемы на работу')
        context['hiring_types'] = EmployeeHiring.HIRING_TYPE_CHOICES

        # Для фильтров
        context['current_hiring_type'] = self.request.GET.get('hiring_type', '')
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['search_query'] = self.request.GET.get('search', '')

        return context


class HiringDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для просмотра детальной информации о приеме на работу
    """
    model = EmployeeHiring
    template_name = 'directory/hiring/detail.html'
    context_object_name = 'hiring'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _(f'Прием на работу: {self.object.employee.full_name_nominative}')

        # Добавляем форму для прикрепления документов
        context['attachment_form'] = DocumentAttachmentForm(
            employee_id=self.object.employee.id,
            initial={'documents': self.object.documents.all()}
        )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Обработка формы прикрепления документов
        if 'attach_documents' in request.POST:
            form = DocumentAttachmentForm(
                request.POST,
                employee_id=self.object.employee.id
            )

            if form.is_valid():
                # Очищаем существующие документы и добавляем выбранные
                self.object.documents.clear()
                selected_docs = form.cleaned_data['documents']
                self.object.documents.add(*selected_docs)
                messages.success(request, _(f'Прикреплено документов: {len(selected_docs)}'))
                return redirect('directory:hiring:hiring_detail', pk=self.object.pk)

        return self.get(request, *args, **kwargs)


class HiringCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой записи о приеме на работу
    """
    model = EmployeeHiring
    form_class = EmployeeHiringRecordForm
    template_name = 'directory/hiring/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Новый прием на работу')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Запись о приеме на работу успешно создана'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('directory:hiring:hiring_detail', kwargs={'pk': self.object.pk})


class HiringUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования записи о приеме на работу
    """
    model = EmployeeHiring
    form_class = EmployeeHiringRecordForm
    template_name = 'directory/hiring/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Редактирование записи о приеме на работу')
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Запись о приеме на работу успешно обновлена'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('directory:hiring:hiring_detail', kwargs={'pk': self.object.pk})


class HiringDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления записи о приеме на работу
    """
    model = EmployeeHiring
    template_name = 'directory/hiring/confirm_delete.html'
    success_url = reverse_lazy('directory:hiring:hiring_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Удаление записи о приеме на работу')
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Запись о приеме на работу успешно удалена'))
        return super().delete(request, *args, **kwargs)


class CreateHiringFromEmployeeView(LoginRequiredMixin, FormView):
    """
    Представление для создания записи о приеме на основе существующего сотрудника
    """
    template_name = 'directory/hiring/create_from_employee.html'
    form_class = forms.Form  # Пустая форма, так как данные берутся из сотрудника

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)
        context['employee'] = employee
        context['title'] = _('Создание записи о приеме из сотрудника')
        return context

    def form_valid(self, form):
        employee_id = self.kwargs.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)

        try:
            hiring = create_hiring_from_employee(employee, self.request.user)
            messages.success(
                self.request,
                _('Запись о приеме на работу успешно создана на основе данных сотрудника')
            )
            return redirect('directory:hiring:hiring_detail', pk=hiring.pk)
        except Exception as e:
            logger.error(f"Ошибка при создании записи о приеме: {e}")
            messages.error(self.request, _('Произошла ошибка при создании записи о приеме'))
            return self.form_invalid(form)