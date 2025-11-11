from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from directory.models import Employee, StructuralSubdivision, Position
from directory.forms import EmployeeForm
from directory.forms.employee_hiring import EmployeeHiringForm
from directory.utils.declension import decline_full_name


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'directory/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по организациям профиля пользователя
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        # Фильтрация по подразделению
        subdivision = self.request.GET.get('subdivision')
        if subdivision:
            queryset = queryset.filter(subdivision_id=subdivision)

        # Фильтрация по должности
        position = self.request.GET.get('position')
        if position:
            queryset = queryset.filter(position_id=position)

        # Поиск по имени
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(full_name_nominative__icontains=search)

        return queryset.select_related('position', 'subdivision', 'organization')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Сотрудники'

        # Фильтрация списков подразделений и должностей по организациям профиля
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            context['subdivisions'] = StructuralSubdivision.objects.filter(organization__in=allowed_orgs)
            context['positions'] = Position.objects.filter(organization__in=allowed_orgs)
        else:
            context['subdivisions'] = StructuralSubdivision.objects.all()
            context['positions'] = Position.objects.all()

        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'directory/employees/form.html'
    success_url = reverse_lazy('directory:employees:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление сотрудника'
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'directory/employees/form.html'

    def get_success_url(self):
        """Перенаправляем на профиль сотрудника после обновления"""
        return reverse('directory:employees:employee_profile', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование сотрудника'
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'directory/employees/confirm_delete.html'
    success_url = reverse_lazy('directory:employees:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление сотрудника'
        return context


class EmployeeProfileView(LoginRequiredMixin, DetailView):
    """
    👤 Представление для просмотра профиля сотрудника с возможностью
    выполнения дополнительных действий
    """
    model = Employee
    template_name = 'directory/employees/profile.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Профиль сотрудника: {self.object.full_name_nominative}'

        # Проверяем, новый ли это сотрудник (для показа уведомления)
        context['is_new_employee'] = self.request.GET.get('new', False)

        # Проверяем, есть ли у сотрудника СИЗ
        if hasattr(self.object, 'position') and self.object.position:
            from directory.models.siz import SIZNorm
            context['has_siz_norms'] = SIZNorm.objects.filter(
                position=self.object.position
            ).exists()

        # Проверяем, есть ли у сотрудника выданные СИЗ
        context['has_issued_siz'] = hasattr(self.object, 'issued_siz') and self.object.issued_siz.exists()

        return context


class EmployeeHiringView(LoginRequiredMixin, FormView):
    """
    👥 Представление для страницы найма сотрудника

    Отображает единую форму найма сотрудника с сохранением логики
    ограничения по организациям из профиля пользователя.
    """
    template_name = 'directory/employees/hire.html'
    form_class = EmployeeHiringForm

    def get_form_kwargs(self):
        """
        🔑 Передаем текущего пользователя в форму
        для ограничения доступных организаций
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """
        📊 Добавляем контекст для шаблона
        """
        context = super().get_context_data(**kwargs)
        context['title'] = '📝 Прием на работу'
        context['current_date'] = timezone.now().date()

        # Получаем недавно принятых сотрудников, с учетом доступных организаций
        user = self.request.user

        # 🔄 Создаем базовый запрос без среза
        recent_employees_query = Employee.objects.all()

        # Ограничиваем по организациям из профиля пользователя
        if not user.is_superuser and hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
            recent_employees_query = recent_employees_query.filter(organization__in=allowed_orgs)

        # Затем сортируем и применяем срез
        recent_employees_query = recent_employees_query.order_by('-id')[:5]

        context['recent_employees'] = recent_employees_query
        # Добавляем типы договоров для отображения в шаблоне
        context['contract_types'] = Employee.CONTRACT_TYPE_CHOICES

        return context

    def form_valid(self, form):
        """
        ✅ Обработка валидной формы с сохранением или предпросмотром
        """
        # Проверяем, нужен ли предпросмотр
        if 'preview' in self.request.POST:
            # Отображаем страницу предпросмотра с данными из формы
            return render(self.request, 'directory/preview.html', {
                'form': form,
                'data': form.cleaned_data
            })

        # Получаем данные из формы
        employee_data = form.cleaned_data

        # Сохраняем данные формы
        employee = form.save()

        # Добавляем сообщение об успешном найме
        messages.success(
            self.request,
            f"✅ Сотрудник {employee.full_name_nominative} успешно принят на работу"
        )

        # Перенаправляем на профиль сотрудника с указанием, что он новый
        return redirect(
            reverse('directory:employees:employee_profile', kwargs={'pk': employee.pk}) + '?new=true'
        )


def get_subdivisions(request):
    """AJAX представление для получения подразделений по организации"""
    organization_id = request.GET.get('organization')
    subdivisions = StructuralSubdivision.objects.filter(
        organization_id=organization_id
    ).values('id', 'name')
    return JsonResponse(list(subdivisions), safe=False)


def get_positions(request):
    """AJAX представление для получения должностей по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    positions = Position.objects.filter(
        subdivision_id=subdivision_id
    ).values('id', 'position_name')  # Изменено с name на position_name
    return JsonResponse(list(positions), safe=False)