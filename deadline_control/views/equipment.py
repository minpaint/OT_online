# deadline_control/views/equipment.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from deadline_control.models import Equipment
from deadline_control.forms import EquipmentForm


class EquipmentListView(LoginRequiredMixin, ListView):
    """Список оборудования с древовидным представлением"""
    model = Equipment
    template_name = 'deadline_control/equipment/list.html'
    context_object_name = 'equipment_list'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs.select_related('organization', 'subdivision', 'department').order_by('equipment_name')


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    """Создание нового оборудования"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'deadline_control/equipment/form.html'
    success_url = reverse_lazy('deadline_control:equipment:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Оборудование "{form.instance.equipment_name}" успешно создано')
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование оборудования"""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'deadline_control/equipment/form.html'
    success_url = reverse_lazy('deadline_control:equipment:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Оборудование "{form.instance.equipment_name}" успешно обновлено')
        return super().form_valid(form)


class EquipmentDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация об оборудовании"""
    model = Equipment
    template_name = 'deadline_control/equipment/detail.html'
    context_object_name = 'equipment'


class EquipmentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление оборудования"""
    model = Equipment
    template_name = 'deadline_control/equipment/confirm_delete.html'
    success_url = reverse_lazy('deadline_control:equipment:list')

    def delete(self, request, *args, **kwargs):
        equipment = self.get_object()
        messages.success(request, f'Оборудование "{equipment.equipment_name}" успешно удалено')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def perform_maintenance(request, pk):
    """Проведение ТО для оборудования"""
    equipment = get_object_or_404(Equipment, pk=pk)

    # Проверка прав доступа
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        if equipment.organization not in allowed_orgs:
            messages.error(request, 'У вас нет прав для выполнения этой операции')
            return redirect('deadline_control:equipment:list')

    date_str = request.POST.get('maintenance_date')
    comment = request.POST.get('comment', '')

    new_date = parse_date(date_str) if date_str else None
    equipment.update_maintenance(new_date=new_date, comment=comment)

    messages.success(request, f'ТО для "{equipment.equipment_name}" успешно проведено')

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'next_date': equipment.next_maintenance_date.isoformat() if equipment.next_maintenance_date else None,
            'days_until': equipment.days_until_maintenance()
        })

    return redirect('deadline_control:equipment:list')
