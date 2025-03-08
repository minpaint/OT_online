# 📁 directory/views/home.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Prefetch, Q

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

        # 🔍 Получаем организации из профиля пользователя
        user = self.request.user
        if hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
        else:
            allowed_orgs = Organization.objects.none()

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

                    # 📂 Формируем структуру отдела
                    dept_data = {
                        'id': department.id,
                        'name': department.name,
                        'employees': list(dept_employees)
                    }

                    sub_data['departments'].append(dept_data)

                org_data['subdivisions'].append(sub_data)

            organizations.append(org_data)

        context['organizations'] = organizations
        return context