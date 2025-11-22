# directory/views/commissions.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Prefetch

from directory.models import Commission, CommissionMember, Employee, Organization, StructuralSubdivision, Department
from directory.forms.commission import CommissionForm, CommissionMemberForm
from directory.utils.commission_service import get_commission_members_formatted
from directory.mixins import AccessControlMixin, AccessControlObjectMixin
from directory.utils.permissions import AccessControlHelper


class CommissionTreeView(LoginRequiredMixin, TemplateView):
    """
    🌳 Древовидное представление комиссий по организационной структуре.

    Отображает иерархическую структуру:
    Организация → Подразделение → Отдел → Комиссия (с участниками)
    """
    template_name = 'directory/commissions/tree_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Комиссии'

        # Получаем все организации, доступные пользователю через AccessControlHelper
        allowed_orgs = AccessControlHelper.get_accessible_organizations(
            self.request.user, self.request
        )

        # Создаем структуру данных для дерева
        tree_data = []

        # Оптимизируем запрос с использованием prefetch_related
        organizations = allowed_orgs.prefetch_related(
            'commissions',
            'commissions__members',
            'commissions__members__employee',
            'commissions__members__employee__position',
            'subdivisions',
            'subdivisions__commissions',
            'subdivisions__commissions__members',
            'subdivisions__commissions__members__employee',
            'subdivisions__commissions__members__employee__position',
            'subdivisions__departments',
            'subdivisions__departments__commissions',
            'subdivisions__departments__commissions__members',
            'subdivisions__departments__commissions__members__employee',
            'subdivisions__departments__commissions__members__employee__position',
        )

        # Иконки для типов комиссий
        commission_type_icons = {
            'ot': '🛡️',  # Охрана труда
            'eb': '⚡',  # Электробезопасность
            'pb': '🔥',  # Пожарная безопасность
            'other': '📋',  # Другие типы
        }

        # Иконки для ролей участников
        role_icons = {
            'chairman': '👑',
            'secretary': '📝',
            'member': '👤',
        }

        # Для каждой организации формируем структуру
        for org in organizations:
            org_data = {
                'id': org.id,
                'name': org.short_name_ru or org.full_name_ru,
                'icon': '🏢',
                'commissions': [],
                'subdivisions': []
            }

            # Получаем комиссии на уровне организации
            org_commissions = Commission.objects.filter(
                organization=org,
                subdivision__isnull=True,
                department__isnull=True
            ).prefetch_related(
                'members',
                'members__employee',
                'members__employee__position'
            )

            # Добавляем комиссии организации
            for commission in org_commissions:
                # Получаем участников комиссии в структурированном виде
                commission_data = get_commission_members_formatted(commission)

                # Тип комиссии и иконка
                commission_type = commission.commission_type
                type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                # Формируем данные комиссии
                comm_data = {
                    'id': commission.id,
                    'name': commission.name,
                    'icon': type_icon,
                    'is_active': commission.is_active,
                    'type': commission.get_commission_type_display(),
                    'level': 'organization',
                    'chairman': commission_data.get('chairman', {}),
                    'secretary': commission_data.get('secretary', {}),
                    'members': commission_data.get('members', []),
                }

                org_data['commissions'].append(comm_data)

            # Получаем подразделения организации
            subdivisions = org.subdivisions.all()

            # Для каждого подразделения получаем его комиссии и отделы
            for subdivision in subdivisions:
                subdiv_data = {
                    'id': subdivision.id,
                    'name': subdivision.name,
                    'icon': '🏭',
                    'commissions': [],
                    'departments': []
                }

                # Получаем комиссии на уровне подразделения
                subdiv_commissions = Commission.objects.filter(
                    organization=org,
                    subdivision=subdivision,
                    department__isnull=True
                ).prefetch_related(
                    'members',
                    'members__employee',
                    'members__employee__position'
                )

                # Добавляем комиссии подразделения
                for commission in subdiv_commissions:
                    commission_data = get_commission_members_formatted(commission)

                    # Тип комиссии и иконка
                    commission_type = commission.commission_type
                    type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                    # Формируем данные комиссии
                    comm_data = {
                        'id': commission.id,
                        'name': commission.name,
                        'icon': type_icon,
                        'is_active': commission.is_active,
                        'type': commission.get_commission_type_display(),
                        'level': 'subdivision',
                        'chairman': commission_data.get('chairman', {}),
                        'secretary': commission_data.get('secretary', {}),
                        'members': commission_data.get('members', []),
                    }

                    subdiv_data['commissions'].append(comm_data)

                # Получаем отделы подразделения
                departments = subdivision.departments.all()

                # Для каждого отдела получаем его комиссии
                for department in departments:
                    dept_data = {
                        'id': department.id,
                        'name': department.name,
                        'icon': '📂',
                        'commissions': []
                    }

                    # Получаем комиссии на уровне отдела
                    dept_commissions = Commission.objects.filter(
                        organization=org,
                        subdivision=subdivision,
                        department=department
                    ).prefetch_related(
                        'members',
                        'members__employee',
                        'members__employee__position'
                    )

                    # Добавляем комиссии отдела
                    for commission in dept_commissions:
                        commission_data = get_commission_members_formatted(commission)

                        # Тип комиссии и иконка
                        commission_type = commission.commission_type
                        type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                        # Формируем данные комиссии
                        comm_data = {
                            'id': commission.id,
                            'name': commission.name,
                            'icon': type_icon,
                            'is_active': commission.is_active,
                            'type': commission.get_commission_type_display(),
                            'level': 'department',
                            'chairman': commission_data.get('chairman', {}),
                            'secretary': commission_data.get('secretary', {}),
                            'members': commission_data.get('members', []),
                        }

                        dept_data['commissions'].append(comm_data)

                    # Добавляем отдел в подразделение, только если у него есть комиссии
                    if dept_data['commissions']:
                        subdiv_data['departments'].append(dept_data)

                # Добавляем подразделение в организацию, только если у него есть комиссии или отделы с комиссиями
                if subdiv_data['commissions'] or any(dept['commissions'] for dept in subdiv_data['departments']):
                    org_data['subdivisions'].append(subdiv_data)

            # Добавляем организацию в дерево, только если у нее есть комиссии или подразделения с комиссиями
            if org_data['commissions'] or any(
                    subdiv['commissions'] or subdiv['departments'] for subdiv in org_data['subdivisions']):
                tree_data.append(org_data)

        context['tree_data'] = tree_data
        context['commission_type_icons'] = commission_type_icons
        context['role_icons'] = role_icons

        return context


class CommissionListView(LoginRequiredMixin, AccessControlMixin, ListView):
    """Список комиссий по проверке знаний"""
    model = Commission
    template_name = 'directory/commissions/list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        """Получение списка комиссий с возможностью фильтрации"""
        # AccessControlMixin автоматически фильтрует по правам доступа
        queryset = super().get_queryset()

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


class CommissionDetailView(LoginRequiredMixin, AccessControlObjectMixin, DetailView):
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


class CommissionUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
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


class CommissionDeleteView(LoginRequiredMixin, AccessControlObjectMixin, DeleteView):
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