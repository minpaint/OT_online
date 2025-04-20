# directory/views/equipment.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q

from directory.models import Equipment, Organization
from directory.forms.equipment import EquipmentForm


class EquipmentListView(LoginRequiredMixin, ListView):
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

        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(maintenance_status=status)

        # Фильтрация по организации (из GET-параметров)
        organization = self.request.GET.get('organization')
        if organization:
            queryset = queryset.filter(organization_id=organization)

        # Поиск по названию или инвентарному номеру
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

        # Добавляем текущую дату для проверки просроченных дат
        context['today'] = timezone.now().date()

        # Добавляем варианты статусов
        context['status_choices'] = Equipment.MAINTENANCE_STATUS_CHOICES

        # Добавляем только организации из профиля пользователя
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            context['organizations'] = self.request.user.profile.organizations.all()
        else:
            context['organizations'] = Organization.objects.all()

        # Добавляем параметры запроса для сохранения фильтрации при пагинации
        context['status'] = self.request.GET.get('status', '')
        context['organization'] = self.request.GET.get('organization', '')
        context['search'] = self.request.GET.get('search', '')

        return context

    def post(self, request, *args, **kwargs):
        """Обработка POST запроса для проведения ТО из списка"""
        # Проверяем, есть ли запрос на проведение ТО
        if 'perform_maintenance' in request.POST:
            equipment_id = request.POST.get('perform_maintenance')

            # Получаем оборудование с проверкой доступа по организации
            if not request.user.is_superuser and hasattr(request.user, 'profile'):
                allowed_orgs = request.user.profile.organizations.all()
                equipment = get_object_or_404(Equipment, id=equipment_id, organization__in=allowed_orgs)
            else:
                equipment = get_object_or_404(Equipment, id=equipment_id)

            # Получаем дату из формы
            date_str = request.POST.get(f'maintenance_date_{equipment_id}')
            new_date = parse_date(date_str) if date_str else None

            # Проводим ТО
            equipment.update_maintenance(new_date=new_date, comment='')
            messages.success(request, f'ТО для "{equipment.equipment_name}" успешно проведено')

            # Возвращаемся на ту же страницу с учетом пагинации и фильтров
            query_params = request.GET.copy()
            return redirect(f"{request.path}?{query_params.urlencode()}")

        # Если это не запрос на проведение ТО, используем стандартный обработчик GET
        return self.get(request, *args, **kwargs)

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

    def get_queryset(self):
        """Ограничиваем доступ к оборудованию только организациями из профиля"""
        qs = super().get_queryset()
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs


class EquipmentDetailView(LoginRequiredMixin, UpdateView):
    model = Equipment
    template_name = 'directory/equipment/detail.html'
    fields = []  # используем собственную форму из шаблона

    def get_queryset(self):
        """Ограничиваем доступ к оборудованию только организациями из профиля"""
        qs = super().get_queryset()
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Детали оборудования: {self.object.equipment_name}'
        context['days_until_maintenance'] = self.object.days_until_maintenance()
        context['today'] = timezone.now().date()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'perform_maintenance':
            # получаем дату и комментарий из формы
            date_str = request.POST.get('maintenance_date')
            comment = request.POST.get('comment', '').strip()
            new_date = parse_date(date_str) if date_str else None
            self.object.update_maintenance(new_date=new_date, comment=comment)
            messages.success(
                request,
                f'ТО для "{self.object.equipment_name}" успешно проведено (дата: {self.object.last_maintenance_date})'
            )
        return redirect('directory:equipment:equipment_detail', pk=self.object.pk)


def perform_maintenance(request, pk):
    # Ограничиваем доступ к оборудованию только организациями из профиля
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        equipment = get_object_or_404(Equipment, pk=pk, organization__in=allowed_orgs)
    else:
        equipment = get_object_or_404(Equipment, pk=pk)

    # без комментария и с текущей датой
    equipment.update_maintenance()
    messages.success(request, f'ТО для "{equipment.equipment_name}" успешно проведено')
    return redirect('directory:equipment:equipment_list')