from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import timedelta

from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Employee,
    Position
)
from deadline_control.models import Equipment, KeyDeadlineCategory
from deadline_control.models.medical_norm import EmployeeMedicalExamination


class HomePageView(LoginRequiredMixin, TemplateView):
    """
    🏠 Главная страница с древовидным списком сотрудников

    Отображает иерархическую структуру организаций, подразделений,
    отделов и сотрудников с возможностью выбора через чекбоксы.
    """
    template_name = 'directory/home.html'

    def get_context_data(self, **kwargs):
        """📊 Получение данных для шаблона"""
        context = super().get_context_data(**kwargs)
        context['title'] = '🏠 Главная'

        # 🔍 Получаем организации из профиля пользователя или все для суперпользователя
        user = self.request.user

        # 🆕 Логика для суперпользователя - показываем все организации
        if user.is_superuser:
            allowed_orgs = Organization.objects.all()
        elif hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
        else:
            allowed_orgs = Organization.objects.none()

        # 🔍 Добавляем поддержку поиска сотрудников
        search_query = self.request.GET.get('search', '')
        selected_status = self.request.GET.get('status', '')
        show_fired = self.request.GET.get('show_fired') == 'true'

        # 👤 Получаем список кандидатов для отдельного блока
        candidate_employees = Employee.objects.filter(status='candidate').select_related('position')

        # Применяем ограничения пользователя к кандидатам
        if not user.is_superuser and hasattr(user, 'profile'):
            candidate_employees = candidate_employees.filter(
                organization__in=user.profile.organizations.all()
            )

        # Если есть поиск, применяем его и к кандидатам
        if search_query:
            candidate_employees = candidate_employees.filter(
                Q(full_name_nominative__icontains=search_query) |
                Q(position__position_name__icontains=search_query)
            )

        # Добавляем кандидатов в контекст
        context['candidate_employees'] = candidate_employees
        context['statuses'] = Employee.EMPLOYEE_STATUS_CHOICES
        context['selected_status'] = selected_status
        context['show_fired'] = show_fired

        # Дашборд «Контроль сроков» по доступным организациям
        today = timezone.now().date()
        warning_date = today + timedelta(days=14)
        dashboard_per_org = []

        for org in allowed_orgs:
            eq_qs = Equipment.objects.filter(organization=org)
            overdue_eq = sum(1 for eq in eq_qs if eq.next_maintenance_date and eq.next_maintenance_date < today)
            upcoming_eq = sum(1 for eq in eq_qs if eq.next_maintenance_date and today <= eq.next_maintenance_date <= warning_date)

            cat_qs = KeyDeadlineCategory.objects.filter(organization=org, is_active=True).prefetch_related('items')
            total_deadlines = sum(cat.items.count() for cat in cat_qs)
            overdue_deadlines = 0
            upcoming_deadlines = 0
            for cat in cat_qs:
                for item in cat.items.all():
                    if item.next_date:
                        if item.next_date < today:
                            overdue_deadlines += 1
                        elif item.next_date <= warning_date:
                            upcoming_deadlines += 1

            med_qs = EmployeeMedicalExamination.objects.filter(employee__organization=org)
            overdue_med = sum(1 for exam in med_qs if exam.next_date and exam.next_date < today)
            upcoming_med = sum(1 for exam in med_qs if exam.next_date and today <= exam.next_date <= warning_date)

            dashboard_per_org.append({
                'org': org,
                'equipment': {'total': eq_qs.count(), 'overdue': overdue_eq, 'upcoming': upcoming_eq},
                'deadlines': {'total': total_deadlines, 'overdue': overdue_deadlines, 'upcoming': upcoming_deadlines},
                'medical': {'total': med_qs.count(), 'overdue': overdue_med, 'upcoming': upcoming_med},
                'overdue_total': overdue_eq + overdue_deadlines + overdue_med,
                'upcoming_total': upcoming_eq + upcoming_deadlines + upcoming_med,
            })

        context['deadline_dashboard'] = {
            'per_org': dashboard_per_org,
            'total_overdue': sum(item['overdue_total'] for item in dashboard_per_org),
            'total_upcoming': sum(item['upcoming_total'] for item in dashboard_per_org),
        }

        if search_query:
            # Для поиска сначала получаем все организации
            all_organizations = allowed_orgs

            # Фильтруем сотрудников по поисковому запросу
            # Исключаем кандидатов и уволенных (если show_fired не включено)
            employee_filter = Q(full_name_nominative__icontains=search_query) | Q(
                position__position_name__icontains=search_query)
            status_filter = ~Q(status='candidate')
            if not show_fired:
                status_filter &= ~Q(status='fired')

            # Статус фильтр из UI
            if selected_status:
                status_filter &= Q(status=selected_status)

            filtered_employees = Employee.objects.filter(status_filter & employee_filter).select_related(
                'organization', 'subdivision', 'department', 'position'
            )

            # Собираем ID организаций, подразделений и отделов с найденными сотрудниками
            org_ids = set(filtered_employees.values_list('organization_id', flat=True))
            sub_ids = set(e.subdivision_id for e in filtered_employees if e.subdivision_id)
            dept_ids = set(e.department_id for e in filtered_employees if e.department_id)

            # Формируем список организаций только с найденными сотрудниками
            allowed_orgs = allowed_orgs.filter(id__in=org_ids)

            # Сохраняем поисковый запрос и результаты поиска для шаблона
            context['search_query'] = search_query
            context['search_results'] = True
            context['filtered_employees'] = filtered_employees
            context['total_found'] = filtered_employees.count()

        # 📝 Подготавливаем данные для древовидной структуры
        organizations = []

        # 📊 Для каждой организации получаем древовидную структуру
        for org in allowed_orgs:
            # 📋 Получаем подразделения организации
            subdivisions = StructuralSubdivision.objects.filter(
                organization=org
            ).prefetch_related(
                Prefetch(
                    'departments',
                    queryset=Department.objects.all()
                )
            )

            # 👥 Получаем сотрудников без подразделения (напрямую в организации),
            # исключая кандидатов и уволенных (если show_fired не включено)
            org_employees_filter = Q(organization=org, subdivision__isnull=True) & ~Q(status='candidate')
            if not show_fired:
                org_employees_filter &= ~Q(status='fired')

            if selected_status:
                org_employees_filter &= Q(status=selected_status)

            org_employees = Employee.objects.filter(org_employees_filter).select_related('position')

            # Если есть поисковый запрос, фильтруем сотрудников
            if search_query:
                org_employees = org_employees.filter(
                    Q(full_name_nominative__icontains=search_query) |
                    Q(position__position_name__icontains=search_query)
                )

            # 🏢 Формируем структуру организации
            org_data = {
                'id': org.id,
                'name': org.full_name_ru,
                'short_name': org.short_name_ru,
                'employees': list(org_employees),
                'subdivisions': []
            }

            # 🏭 Для каждого подразделения получаем отделы и сотрудников
            for subdivision in subdivisions:
                # 👥 Сотрудники подразделения без отдела
                # исключая кандидатов и уволенных (если show_fired не включено)
                sub_employees_filter = Q(subdivision=subdivision, department__isnull=True) & ~Q(status='candidate')
                if not show_fired:
                    sub_employees_filter &= ~Q(status='fired')

                if selected_status:
                    sub_employees_filter &= Q(status=selected_status)

                sub_employees = Employee.objects.filter(sub_employees_filter).select_related('position')

                # Если есть поисковый запрос, фильтруем сотрудников
                if search_query:
                    sub_employees = sub_employees.filter(
                        Q(full_name_nominative__icontains=search_query) |
                        Q(position__position_name__icontains=search_query)
                    )

                # 🏭 Формируем структуру подразделения
                sub_data = {
                    'id': subdivision.id,
                    'name': subdivision.name,
                    'employees': list(sub_employees),
                    'departments': []
                }

                # 📂 Для каждого отдела получаем сотрудников
                for department in subdivision.departments.all():
                    # 👥 Сотрудники отдела
                    # исключая кандидатов и уволенных (если show_fired не включено)
                    dept_employees_filter = Q(department=department) & ~Q(status='candidate')
                    if not show_fired:
                        dept_employees_filter &= ~Q(status='fired')

                    if selected_status:
                        dept_employees_filter &= Q(status=selected_status)

                    dept_employees = Employee.objects.filter(dept_employees_filter).select_related('position')

                    # Если есть поисковый запрос, фильтруем сотрудников
                    if search_query:
                        dept_employees = dept_employees.filter(
                            Q(full_name_nominative__icontains=search_query) |
                            Q(position__position_name__icontains=search_query)
                        )

                    # 📂 Формируем структуру отдела
                    dept_data = {
                        'id': department.id,
                        'name': department.name,
                        'employees': list(dept_employees)
                    }

                    sub_data['departments'].append(dept_data)

                # Добавляем подразделение только если в нем есть сотрудники (учитывая поиск)
                if search_query:
                    if sub_employees.count() > 0 or any(len(dept['employees']) > 0 for dept in sub_data['departments']):
                        org_data['subdivisions'].append(sub_data)
                else:
                    org_data['subdivisions'].append(sub_data)

            # Добавляем организацию, если она не пустая в контексте поиска
            if not search_query or org_employees.count() > 0 or any(
                    len(sub['employees']) > 0 for sub in org_data['subdivisions']):
                organizations.append(org_data)

        # 📄 Добавляем пагинацию организаций
        page = self.request.GET.get('page', 1)
        paginator = Paginator(organizations, 5)  # По 5 организаций на страницу

        try:
            organizations_page = paginator.page(page)
        except PageNotAnInteger:
            organizations_page = paginator.page(1)
        except EmptyPage:
            organizations_page = paginator.page(paginator.num_pages)

        context['organizations'] = organizations_page
        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1

        return context
