# deadline_control/views/key_deadline.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from collections import defaultdict

from deadline_control.models import KeyDeadlineCategory, KeyDeadlineItem
from directory.mixins import AccessControlMixin, AccessControlObjectMixin


class KeyDeadlineListView(LoginRequiredMixin, AccessControlMixin, ListView):
    """Список категорий ключевых сроков, сгруппированных по организациям"""
    model = KeyDeadlineCategory
    template_name = 'deadline_control/key_deadline/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # AccessControlMixin автоматически фильтрует по правам доступа
        qs = super().get_queryset()
        return qs.select_related('organization').prefetch_related('items').order_by('organization__short_name_ru', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Группируем категории по организациям
        categories_by_org = defaultdict(list)
        for category in context['categories']:
            categories_by_org[category.organization].append(category)

        # Преобразуем в отсортированный список кортежей (организация, список категорий)
        context['categories_by_organization'] = sorted(
            categories_by_org.items(),
            key=lambda x: x[0].short_name_ru or x[0].full_name_ru
        )

        return context


class KeyDeadlineCategoryCreateView(LoginRequiredMixin, CreateView):
    """Создание новой категории"""
    model = KeyDeadlineCategory
    template_name = 'deadline_control/key_deadline/category_form.html'
    fields = ['name', 'organization', 'description', 'is_active']
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def form_valid(self, form):
        messages.success(self.request, f'Категория "{form.instance.name}" успешно создана')
        return super().form_valid(form)


class KeyDeadlineCategoryUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
    """Редактирование категории"""
    model = KeyDeadlineCategory
    template_name = 'deadline_control/key_deadline/category_form.html'
    fields = ['name', 'organization', 'description', 'is_active']
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def form_valid(self, form):
        messages.success(self.request, f'Категория "{form.instance.name}" успешно обновлена')
        return super().form_valid(form)


class KeyDeadlineCategoryDeleteView(LoginRequiredMixin, AccessControlObjectMixin, DeleteView):
    """Удаление категории"""
    model = KeyDeadlineCategory
    template_name = 'deadline_control/key_deadline/category_confirm_delete.html'
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Категория "{category.name}" успешно удалена')
        return super().delete(request, *args, **kwargs)


class KeyDeadlineItemCreateView(LoginRequiredMixin, CreateView):
    """Создание нового мероприятия"""
    model = KeyDeadlineItem
    template_name = 'deadline_control/key_deadline/item_form.html'
    fields = ['category', 'name', 'periodicity_months', 'current_date', 'responsible_person', 'notes']
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def form_valid(self, form):
        messages.success(self.request, f'Мероприятие "{form.instance.name}" успешно создано')
        return super().form_valid(form)


class KeyDeadlineItemUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
    """Редактирование мероприятия"""
    model = KeyDeadlineItem
    template_name = 'deadline_control/key_deadline/item_form.html'
    fields = ['category', 'name', 'periodicity_months', 'current_date', 'responsible_person', 'notes']
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def form_valid(self, form):
        messages.success(self.request, f'Мероприятие "{form.instance.name}" успешно обновлено')
        return super().form_valid(form)


class KeyDeadlineItemDeleteView(LoginRequiredMixin, AccessControlObjectMixin, DeleteView):
    """Удаление мероприятия"""
    model = KeyDeadlineItem
    template_name = 'deadline_control/key_deadline/item_confirm_delete.html'
    success_url = reverse_lazy('deadline_control:key_deadline:list')

    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        messages.success(request, f'Мероприятие "{item.name}" успешно удалено')
        return super().delete(request, *args, **kwargs)
