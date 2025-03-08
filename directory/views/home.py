# 📁 directory/views/home.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Employee,
    Position
)


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
        if search_query:
            # Для поиска сначала получаем все организации
            all_organizations = allowed_orgs

            # Фильтруем сотрудников по поисковому запросу
            filtered_employees = Employee.objects.filter(
                Q(full_name_nominative__icontains=search_query) |
                Q(position__position_name__icontains=search_query)
            ).select_related('organization', 'subdivision', 'department', 'position')

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

            # 👥 Получаем сотрудников без подразделения (напрямую в организации)
            org_employees = Employee.objects.filter(
                organization=org,
                subdivision__isnull=True
            ).select_related('position')

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
                sub_employees = Employee.objects.filter(
                    subdivision=subdivision,
                    department__isnull=True
                ).select_related('position')

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
                    dept_employees = Employee.objects.filter(
                        department=department
                    ).select_related('position')

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