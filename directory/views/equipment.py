# directory/views/equipment.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from directory.models import Equipment
from directory.forms.equipment import EquipmentForm


class EquipmentListView(LoginRequiredMixin, ListView):
    """
    ⚙️ Представление для отображения списка оборудования.
    С возможностью фильтрации и поиска.
    """
    model = Equipment
    template_name = 'directory/equipment/list.html'
    context_object_name = 'equipment_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по организациям из профиля пользователя
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        # Фильтрация по параметрам из GET-запроса
        organization = self.request.GET.get('organization')
        if organization:
            queryset = queryset.filter(organization_id=organization)

        subdivision = self.request.GET.get('subdivision')
        if subdivision:
            queryset = queryset.filter(subdivision_id=subdivision)

        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)

        maintenance_status = self.request.GET.get('maintenance_status')
        if maintenance_status:
            queryset = queryset.filter(maintenance_status=maintenance_status)

        # Фильтрация по необходимости ТО
        maintenance_filter = self.request.GET.get('maintenance_filter')
        if maintenance_filter == 'required':
            today = timezone.now().date()
            queryset = queryset.filter(next_maintenance_date__lte=today + timezone.timedelta(days=7))
        elif maintenance_filter == 'overdue':
            today = timezone.now().date()
            queryset = queryset.filter(next_maintenance_date__lt=today)

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(equipment_name__icontains=search) |
                Q(inventory_number__icontains=search)
            )

        return queryset.select_related('organization', 'subdivision', 'department')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Оборудование'

        # Статистика для дашборда
        today = timezone.now().date()
        context['equipment_requiring_maintenance'] = Equipment.objects.filter(
            next_maintenance_date__lte=today + timezone.timedelta(days=7)
        ).count()

        context['equipment_overdue'] = Equipment.objects.filter(
            next_maintenance_date__lt=today
        ).count()

        # Сохраняем параметры фильтрации
        context['filters'] = {
            'organization': self.request.GET.get('organization', ''),
            'subdivision': self.request.GET.get('subdivision', ''),
            'department': self.request.GET.get('department', ''),
            'maintenance_status': self.request.GET.get('maintenance_status', ''),
            'maintenance_filter': self.request.GET.get('maintenance_filter', ''),
            'search': self.request.GET.get('search', ''),
        }

        return context


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    """
    ⚙️ Представление для создания нового оборудования.
    """
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
    """
    ⚙️ Представление для редактирования оборудования.
    """
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
    """
    ⚙️ Представление для удаления оборудования.
    """
    model = Equipment
    template_name = 'directory/equipment/confirm_delete.html'
    success_url = reverse_lazy('directory:equipment:equipment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление оборудования'
        return context


class EquipmentDetailView(LoginRequiredMixin, UpdateView):
    """
    ⚙️ Представление для просмотра деталей оборудования.
    Включает функционал проведения ТО.
    """
    model = Equipment
    template_name = 'directory/equipment/detail.html'
    fields = []  # Пустой список, форма только для отображения

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Детали оборудования: {self.object.equipment_name}'

        # Добавляем информацию о техническом обслуживании
        if self.object.maintenance_history:
            context['maintenance_history'] = [
                {'date': date} for date in self.object.maintenance_history
            ]
        else:
            context['maintenance_history'] = []

        context['days_until_maintenance'] = self.object.days_until_maintenance()
        context['is_maintenance_required'] = self.object.is_maintenance_required()

        return context

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает запросы на обновление ТО.
        """
        self.object = self.get_object()
        action = request.POST.get('action')

        if action == 'perform_maintenance':
            self.object.update_maintenance()
            messages.success(request, f'Техническое обслуживание для "{self.object.equipment_name}" успешно проведено')

        return redirect('directory:equipment:equipment_detail', pk=self.object.pk)


def perform_maintenance(request, pk):
    """
    Функция представления для проведения ТО из списка оборудования.
    """
    equipment = get_object_or_404(Equipment, pk=pk)
    equipment.update_maintenance()
    messages.success(request, f'Техническое обслуживание для "{equipment.equipment_name}" успешно проведено')
    return redirect('directory:equipment:equipment_list')