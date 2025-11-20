from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from directory.models import Position, Organization, StructuralSubdivision, Department  # добавляем Department
from directory.forms import PositionForm
from directory.mixins import AccessControlMixin, AccessControlObjectMixin
from directory.utils.permissions import AccessControlHelper

class PositionListView(LoginRequiredMixin, AccessControlMixin, ListView):
    model = Position
    template_name = 'directory/positions/list.html'
    context_object_name = 'positions'
    paginate_by = 20

    def get_queryset(self):
        # AccessControlMixin автоматически фильтрует по правам доступа
        queryset = super().get_queryset()

        # Фильтрация по организации (из GET-параметров)
        organization = self.request.GET.get('organization')
        if organization:
            queryset = queryset.filter(organization_id=organization)

        # Фильтрация по подразделению
        subdivision = self.request.GET.get('subdivision')
        if subdivision:
            queryset = queryset.filter(subdivision_id=subdivision)

        # Поиск по названию должности
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(position_name__icontains=search)

        return queryset.select_related('organization', 'subdivision', 'department')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Должности'

        # Используем AccessControlHelper для получения доступных организаций и подразделений
        context['organizations'] = AccessControlHelper.get_accessible_organizations(
            self.request.user, self.request
        )
        context['subdivisions'] = AccessControlHelper.get_accessible_subdivisions(
            self.request.user, self.request
        )

        return context

class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'directory/positions/form.html'
    success_url = reverse_lazy('directory:positions:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление должности'
        return context

class PositionUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'directory/positions/form.html'
    success_url = reverse_lazy('directory:positions:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование должности'
        return context

class PositionDeleteView(LoginRequiredMixin, AccessControlObjectMixin, DeleteView):
    model = Position
    template_name = 'directory/positions/confirm_delete.html'
    success_url = reverse_lazy('directory:positions:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление должности'
        return context

def get_positions(request):
    """AJAX представление для получения должностей по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    positions = Position.objects.filter(
        subdivision_id=subdivision_id
    ).values('id', 'position_name')  # Используем position_name вместо name
    return JsonResponse(list(positions), safe=False)


def get_departments(request):
    """AJAX представление для получения отделов по организации и подразделению"""
    organization_id = request.GET.get('organization')
    subdivision_id = request.GET.get('subdivision')

    departments = Department.objects.filter(
        organization_id=organization_id,
        subdivision_id=subdivision_id
    ).values('id', 'name')

    return JsonResponse(list(departments), safe=False)