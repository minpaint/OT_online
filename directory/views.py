# 📁 directory/views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Position, Organization, StructuralSubdivision, Department, Employee

class HomeView(TemplateView):
    template_name = 'directory/home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_employees': Employee.objects.count(),
            'total_positions': Position.objects.count(),
            'total_organizations': Organization.objects.count(),
            'total_subdivisions': StructuralSubdivision.objects.count(),
        })
        return context

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'directory/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20
    def get_queryset(self):
        queryset = Employee.objects.select_related('subdivision', 'position', 'organization', 'department').order_by('full_name_nominative')
        if organization_id := self.request.GET.get('organization'):
            queryset = queryset.filter(organization_id=organization_id)
        if subdivision_id := self.request.GET.get('subdivision'):
            queryset = queryset.filter(subdivision_id=subdivision_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'organizations': Organization.objects.all(),
            'subdivisions': StructuralSubdivision.objects.all(),
            'selected_organization': self.request.GET.get('organization'),
            'selected_subdivision': self.request.GET.get('subdivision'),
        })
        return context

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    template_name = 'directory/employees/form.html'
    fields = [
        'full_name_nominative',
        'full_name_dative',
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor',
        'date_of_birth',
        'place_of_residence',
        'height',
        'clothing_size',
        'shoe_size'
    ]
    success_url = reverse_lazy('directory:employee_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление сотрудника'
        return context

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    template_name = 'directory/employees/form.html'
    fields = [
        'full_name_nominative',
        'full_name_dative',
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor',
        'date_of_birth',
        'place_of_residence',
        'height',
        'clothing_size',
        'shoe_size'
    ]
    success_url = reverse_lazy('directory:employee_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование сотрудника'
        return context

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'directory/employees/confirm_delete.html'
    success_url = reverse_lazy('directory:employee_list')

class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    template_name = 'directory/positions/list.html'
    context_object_name = 'positions'
    paginate_by = 10
    def get_queryset(self):
        queryset = Position.objects.select_related('organization', 'subdivision', 'department').prefetch_related('documents', 'equipment').order_by('position_name')
        if organization_id := self.request.GET.get('organization'):
            queryset = queryset.filter(organization_id=organization_id)
        if subdivision_id := self.request.GET.get('subdivision'):
            queryset = queryset.filter(subdivision_id=subdivision_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Должности',
            'selected_organization': self.request.GET.get('organization'),
            'selected_subdivision': self.request.GET.get('subdivision'),
            'organizations': Organization.objects.all().order_by('full_name_ru'),
            'subdivisions': StructuralSubdivision.objects.all().order_by('name'),
        })
        return context

class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    template_name = 'directory/positions/form.html'
    fields = '__all__'
    success_url = reverse_lazy('directory:position_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление должности'
        return context

class PositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Position
    template_name = 'directory/positions/form.html'
    fields = '__all__'
    success_url = reverse_lazy('directory:position_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование должности'
        return context

class PositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Position
    template_name = 'directory/positions/confirm_delete.html'
    success_url = reverse_lazy('directory:position_list')

def get_subdivisions(request):
    organization_id = request.GET.get('organization')
    subdivisions = StructuralSubdivision.objects.filter(organization_id=organization_id).order_by('name').values('id', 'name')
    return JsonResponse(list(subdivisions), safe=False)

def get_positions(request):
    subdivision_id = request.GET.get('subdivision')
    positions = Position.objects.filter(subdivision_id=subdivision_id).order_by('position_name').values('id', 'position_name')
    return JsonResponse(list(positions), safe=False)

def get_departments(request):
    subdivision_id = request.GET.get('subdivision')
    departments = Department.objects.filter(subdivision_id=subdivision_id).order_by('name').values('id', 'name')
    return JsonResponse(list(departments), safe=False)
