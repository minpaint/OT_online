# directory/views/commissions.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from directory.models import Commission, CommissionMember, Employee
from directory.forms.commission import CommissionForm, CommissionMemberForm


class CommissionListView(LoginRequiredMixin, ListView):
    """Список комиссий по проверке знаний"""
    model = Commission
    template_name = 'directory/commissions/list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        """Получение списка комиссий с возможностью фильтрации"""
        queryset = Commission.objects.all()

        # Фильтрация по активности
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Фильтрация по типу комиссии
        commission_type = self.request.GET.get('commission_type')
        if commission_type:
            queryset = queryset.filter(commission_type=commission_type)

        # Фильтрация по уровню (организация, подразделение, отдел)
        level = self.request.GET.get('level')
        if level == 'org':
            queryset = queryset.filter(organization__isnull=False)
        elif level == 'sub':
            queryset = queryset.filter(subdivision__isnull=False)
        elif level == 'dep':
            queryset = queryset.filter(department__isnull=False)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список комиссий по проверке знаний'

        # Добавление фильтров
        context['filter_is_active'] = self.request.GET.get('is_active', '')
        context['filter_commission_type'] = self.request.GET.get('commission_type', '')
        context['filter_level'] = self.request.GET.get('level', '')

        return context


class CommissionDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о комиссии"""
    model = Commission
    template_name = 'directory/commissions/detail.html'
    context_object_name = 'commission'

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        commission = self.object
        context['title'] = f'Комиссия: {commission.name}'

        # Получаем всех членов комиссии
        context['chairman'] = commission.members.filter(role='chairman', is_active=True).first()
        context['secretary'] = commission.members.filter(role='secretary', is_active=True).first()
        context['members'] = commission.members.filter(role='member', is_active=True)

        # Проверка полноты состава комиссии
        has_chairman = context['chairman'] is not None
        has_secretary = context['secretary'] is not None
        has_members = context['members'].exists()

        if not (has_chairman and has_secretary and has_members):
            missing = []
            if not has_chairman:
                missing.append('председатель')
            if not has_secretary:
                missing.append('секретарь')
            if not has_members:
                missing.append('члены комиссии')

            context['warning_message'] = f"В комиссии отсутствуют: {', '.join(missing)}."

        return context


class CommissionCreateView(LoginRequiredMixin, CreateView):
    """Создание новой комиссии"""
    model = Commission
    form_class = CommissionForm
    template_name = 'directory/commissions/form.html'

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание новой комиссии'
        return context

    def form_valid(self, form):
        """Обработка успешной валидации формы"""
        messages.success(self.request, 'Комиссия успешно создана')
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращаем URL для переадресации"""
        return reverse_lazy('directory:commissions:commission_detail', kwargs={'pk': self.object.pk})


class CommissionUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование существующей комиссии"""
    model = Commission
    form_class = CommissionForm
    template_name = 'directory/commissions/form.html'

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование комиссии: {self.object.name}'
        return context

    def form_valid(self, form):
        """Обработка успешной валидации формы"""
        messages.success(self.request, 'Комиссия успешно обновлена')
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращаем URL для переадресации"""
        return reverse_lazy('directory:commissions:commission_detail', kwargs={'pk': self.object.pk})


class CommissionDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комиссии"""
    model = Commission
    template_name = 'directory/commissions/confirm_delete.html'
    success_url = reverse_lazy('directory:commissions:commission_list')

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление комиссии: {self.object.name}'
        return context

    def delete(self, request, *args, **kwargs):
        """Переопределение метода удаления"""
        messages.success(request, 'Комиссия успешно удалена')
        return super().delete(request, *args, **kwargs)


class CommissionMemberCreateView(LoginRequiredMixin, CreateView):
    """Добавление участника в комиссию"""
    model = CommissionMember
    form_class = CommissionMemberForm
    template_name = 'directory/commissions/member_form.html'

    def get_initial(self):
        """Предустановка начальных значений формы"""
        initial = super().get_initial()
        commission_id = self.kwargs.get('commission_id')
        if commission_id:
            initial['commission'] = Commission.objects.get(id=commission_id)
        return initial

    def get_form_kwargs(self):
        """Передача дополнительных аргументов в форму"""
        kwargs = super().get_form_kwargs()
        commission_id = self.kwargs.get('commission_id')
        if commission_id:
            commission = Commission.objects.get(id=commission_id)
            kwargs['commission'] = commission
        return kwargs

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        commission_id = self.kwargs.get('commission_id')
        if commission_id:
            commission = Commission.objects.get(id=commission_id)
            context['commission'] = commission
            context['title'] = f'Добавление участника в комиссию: {commission.name}'
        return context

    def form_valid(self, form):
        """Обработка успешной валидации формы"""
        messages.success(self.request, 'Участник успешно добавлен в комиссию')
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращаем URL для переадресации"""
        return reverse_lazy('directory:commissions:commission_detail', kwargs={'pk': self.object.commission.pk})


class CommissionMemberUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование участника комиссии"""
    model = CommissionMember
    form_class = CommissionMemberForm
    template_name = 'directory/commissions/member_form.html'

    def get_form_kwargs(self):
        """Передача дополнительных аргументов в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['commission'] = self.object.commission
        return kwargs

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['commission'] = self.object.commission
        context['title'] = f'Редактирование участника комиссии: {self.object.employee.full_name_nominative}'
        return context

    def form_valid(self, form):
        """Обработка успешной валидации формы"""
        messages.success(self.request, 'Данные участника успешно обновлены')
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращаем URL для переадресации"""
        return reverse_lazy('directory:commissions:commission_detail', kwargs={'pk': self.object.commission.pk})


class CommissionMemberDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление участника комиссии"""
    model = CommissionMember
    template_name = 'directory/commissions/member_confirm_delete.html'

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление участника комиссии: {self.object.employee.full_name_nominative}'
        return context

    def delete(self, request, *args, **kwargs):
        """Переопределение метода удаления"""
        messages.success(request, 'Участник успешно удален из комиссии')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        """Возвращаем URL для переадресации"""
        commission_id = self.object.commission.id
        return reverse_lazy('directory:commissions:commission_detail', kwargs={'pk': commission_id})