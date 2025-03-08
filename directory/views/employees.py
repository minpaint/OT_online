from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages

from directory.models import Employee, StructuralSubdivision, Position
from directory.forms import EmployeeForm
from directory.forms.employee_hiring import EmployeeHiringForm


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'directory/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтрация
        subdivision = self.request.GET.get('subdivision')
        if subdivision:
            queryset = queryset.filter(subdivision_id=subdivision)

        position = self.request.GET.get('position')
        if position:
            queryset = queryset.filter(position_id=position)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(full_name_nominative__icontains=search)

        return queryset.select_related('position', 'subdivision', 'organization')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Сотрудники'
        context['subdivisions'] = StructuralSubdivision.objects.all()
        context['positions'] = Position.objects.all()
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'directory/employees/form.html'
    success_url = reverse_lazy('directory:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление сотрудника'
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'directory/employees/form.html'
    success_url = reverse_lazy('directory:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование сотрудника'
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'directory/employees/confirm_delete.html'
    success_url = reverse_lazy('directory:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление сотрудника'
        return context


class EmployeeHiringView(LoginRequiredMixin, FormView):
    """
    👥 Представление для страницы найма сотрудника

    Отображает форму найма сотрудника с сохранением логики
    ограничения по организациям из профиля пользователя.
    """
    template_name = 'directory/employees/hire.html'
    form_class = EmployeeHiringForm
    success_url = reverse_lazy('directory:employees:employee_list')

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

        # Получаем недавно принятых сотрудников, с учетом доступных организаций
        user = self.request.user

        # 🔄 ИСПРАВЛЕНИЕ: сначала создаем базовый запрос без среза
        recent_employees_query = Employee.objects.all()

        # Ограничиваем по организациям из профиля пользователя
        if not user.is_superuser and hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
            recent_employees_query = recent_employees_query.filter(organization__in=allowed_orgs)

        # Затем сортируем и применяем срез
        recent_employees_query = recent_employees_query.order_by('-id')[:5]

        context['recent_employees'] = recent_employees_query

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

        # Сохраняем данные формы
        employee = form.save()

        # Добавляем сообщение об успешном найме
        messages.success(
            self.request,
            f"✅ Сотрудник {employee.full_name_nominative} успешно принят на работу"
        )

        return super().form_valid(form)


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