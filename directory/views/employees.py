from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from directory.models import Employee, StructuralSubdivision, Position
from directory.forms import EmployeeForm


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

        return queryset.select_related('position', 'subdivision')

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
    success_url = reverse_lazy('directory:employee-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление сотрудника'
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'directory/employees/form.html'
    success_url = reverse_lazy('employee-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование сотрудника'
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'directory/employees/confirm_delete.html'
    success_url = reverse_lazy('employee-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление сотрудника'
        return context


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
    ).values('id', 'name')
    return JsonResponse(list(positions), safe=False)