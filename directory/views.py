from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import (
    Position,
    Organization,
    StructuralSubdivision,  # Изменено с Subdivision на StructuralSubdivision
    Department,
    Employee
)

class HomeView(TemplateView):
    """Представление главной страницы"""
    template_name = 'directory/home.html'

# Представления для сотрудников
class EmployeeListView(LoginRequiredMixin, ListView):
    """Представление списка сотрудников"""
    model = Employee
    template_name = 'directory/employees/list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        return Employee.objects.all().order_by('full_name')

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания нового сотрудника"""
    model = Employee
    template_name = 'directory/employees/form.html'
    fields = ['full_name', 'subdivision', 'position', 'date_of_employment', 'salary']
    success_url = reverse_lazy('directory:employee-list')

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования существующего сотрудника"""
    model = Employee
    template_name = 'directory/employees/form.html'
    fields = ['full_name', 'subdivision', 'position', 'date_of_employment', 'salary']
    success_url = reverse_lazy('directory:employee-list')

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления сотрудника"""
    model = Employee
    template_name = 'directory/employees/confirm_delete.html'
    success_url = reverse_lazy('directory:employee-list')

# Представления для должностей
class PositionListView(LoginRequiredMixin, ListView):
    """Представление списка должностей с фильтрацией и пагинацией"""
    model = Position
    template_name = 'directory/positions/list.html'
    context_object_name = 'positions'
    paginate_by = 10

    def get_queryset(self):
        queryset = Position.objects.select_related(
            'organization',
            'subdivision',
            'department'
        ).order_by('position_name')

        organization_id = self.request.GET.get('organization')
        subdivision_id = self.request.GET.get('subdivision')

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if subdivision_id:
            queryset = queryset.filter(subdivision_id=subdivision_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Должности',
            'selected_organization': self.request.GET.get('organization'),
            'selected_subdivision': self.request.GET.get('subdivision'),
            'organizations': Organization.objects.all().order_by('full_name_ru'),
            'subdivisions': StructuralSubdivision.objects.all().order_by('name'),  # Изменено
        })
        return context

class PositionCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания новой должности"""
    model = Position
    template_name = 'directory/positions/form.html'
    fields = ['position_name', 'organization', 'subdivision', 'department', 'electrical_safety_group']
    success_url = reverse_lazy('directory:position-list')

class PositionUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования существующей должности"""
    model = Position
    template_name = 'directory/positions/form.html'
    fields = ['position_name', 'organization', 'subdivision', 'department', 'electrical_safety_group']
    success_url = reverse_lazy('directory:position-list')

class PositionDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления должности"""
    model = Position
    template_name = 'directory/positions/confirm_delete.html'
    success_url = reverse_lazy('directory:position-list')

# AJAX представления
def get_subdivisions(request):
    """Получение списка подразделений по организации"""
    organization_id = request.GET.get('organization')
    subdivisions = StructuralSubdivision.objects.filter(  # Изменено
        organization_id=organization_id
    ).order_by('name')
    data = [{'id': s.id, 'name': s.name} for s in subdivisions]
    return JsonResponse(data, safe=False)

def get_positions(request):
    """Получение списка должностей по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    positions = Position.objects.filter(
        subdivision_id=subdivision_id
    ).order_by('position_name')
    data = [{'id': p.id, 'name': p.position_name} for p in positions]
    return JsonResponse(data, safe=False)

def get_departments(request):
    """Получение списка отделов по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    departments = Department.objects.filter(
        subdivision_id=subdivision_id
    ).order_by('name')
    data = [{'id': d.id, 'name': d.name} for d in departments]
    return JsonResponse(data, safe=False)