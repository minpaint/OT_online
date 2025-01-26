from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from directory.models import Position, Organization, StructuralSubdivision
from directory.forms import PositionForm

class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    template_name = 'directory/positions/list.html'
    context_object_name = 'positions'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтрация
        organization = self.request.GET.get('organization')
        if organization:
            queryset = queryset.filter(organization_id=organization)
        subdivision = self.request.GET.get('subdivision')
        if subdivision:
            queryset = queryset.filter(subdivision_id=subdivision)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(position_name__icontains=search)
        return queryset.select_related('organization', 'subdivision', 'department')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Должности'
        context['organizations'] = Organization.objects.all()
        context['subdivisions'] = StructuralSubdivision.objects.all()
        return context

class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'directory/positions/form.html'
    success_url = reverse_lazy('directory:position-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление должности'
        return context

class PositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'directory/positions/form.html'
    success_url = reverse_lazy('directory:position-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование должности'
        return context

class PositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Position
    template_name = 'directory/positions/confirm_delete.html'
    success_url = reverse_lazy('directory:position-list')

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