# directory/views/equipment.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q

from directory.models import Equipment
from directory.forms.equipment import EquipmentForm


class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'directory/equipment/list.html'
    context_object_name = 'equipment_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # ... (фильтры без изменений) ...
        return queryset.select_related('organization', 'subdivision', 'department')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ... (контекст без изменений) ...
        return context


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'directory/equipment/form.html'
    success_url = reverse_lazy('directory:equipment:equipment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление оборудования'
        return context


class EquipmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'directory/equipment/form.html'
    success_url = reverse_lazy('directory:equipment:equipment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование оборудования'
        return context


class EquipmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Equipment
    template_name = 'directory/equipment/confirm_delete.html'
    success_url = reverse_lazy('directory:equipment:equipment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление оборудования'
        return context


class EquipmentDetailView(LoginRequiredMixin, UpdateView):
    model = Equipment
    template_name = 'directory/equipment/detail.html'
    fields = []  # используем собственную форму из шаблона

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Детали оборудования: {self.object.equipment_name}'
        context['days_until_maintenance'] = self.object.days_until_maintenance()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'perform_maintenance':
            # получаем дату и комментарий из формы
            date_str = request.POST.get('maintenance_date')
            comment  = request.POST.get('comment', '').strip()
            new_date = parse_date(date_str) if date_str else None
            self.object.update_maintenance(new_date=new_date, comment=comment)
            messages.success(
                request,
                f'ТО для "{self.object.equipment_name}" успешно проведено (дата: {self.object.last_maintenance_date})'
            )
        return redirect('directory:equipment:equipment_detail', pk=self.object.pk)


def perform_maintenance(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    # без комментария и с текущей датой
    equipment.update_maintenance()
    messages.success(request, f'ТО для "{equipment.equipment_name}" успешно проведено')
    return redirect('directory:equipment:equipment_list')
