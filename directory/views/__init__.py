from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Prefetch

from directory.forms import EmployeeHiringForm
from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Employee,
    Position
)
from .auth import UserRegistrationView

# Импортируем представления для сотрудников
from .employees import (
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    EmployeeHiringView,
    EmployeeProfileView, # Добавляем новое представление
    get_subdivisions
)

# Импортируем представления для должностей
from .positions import (
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
    get_positions,
    get_departments
)

# Импортируем представления из новой модульной структуры документов
# Используем абсолютный импорт, чтобы избежать конфликтов
from directory.views.documents import (
    DocumentSelectionView,
    GeneratedDocumentListView,
    document_download,
)

# Импортируем представления для выдачи СИЗ
from .siz_issued import (
    SIZIssueFormView,
    SIZPersonalCardView,
    SIZIssueReturnView,
    employee_siz_issued_list,
)

# Представления для медосмотров перемещены в deadline_control

# Импортируем представление вводного инструктажа
from .home import IntroductoryBriefingView


class HomePageView(LoginRequiredMixin, TemplateView):
    """
    🏠 Главная страница с древовидным списком сотрудников

    Отображает иерархическую структуру организаций, подразделений,
    отделов и сотрудников с возможностью выбора через чекбоксы.
    """
    template_name = 'directory/home.html'

    def get_context_data(self, **kwargs):
        """📊 Получение данных для шаблона"""
        from django.utils import timezone
        from datetime import timedelta
        from deadline_control.models import Equipment, KeyDeadlineCategory
        from deadline_control.models.medical_norm import EmployeeMedicalExamination

        context = super().get_context_data(**kwargs)
        context['title'] = '🏠 Главная'

        # 🔍 Получаем организации из профиля пользователя
        user = self.request.user
        if user.is_superuser:
            # Суперпользователь видит все организации
            allowed_orgs = Organization.objects.all()
        elif hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
        else:
            allowed_orgs = Organization.objects.none()

        # 📝 Подготавливаем данные для древовидной структуры
        organizations = []

        # ⏰ Данные для дашборда контроля сроков (как в DashboardView)
        today = timezone.now().date()
        warning_date = today + timedelta(days=14)

        # Оборудование
        equipment_qs = Equipment.objects.select_related('organization', 'subdivision', 'department')
        if not user.is_superuser and allowed_orgs.exists():
            equipment_qs = equipment_qs.filter(organization__in=allowed_orgs)

        overdue_equipment = []
        upcoming_equipment = []
        for eq in equipment_qs:
            if eq.next_maintenance_date:
                if eq.next_maintenance_date < today:
                    overdue_equipment.append(eq)
                elif eq.next_maintenance_date <= warning_date:
                    upcoming_equipment.append(eq)

        # Ключевые сроки
        categories_qs = KeyDeadlineCategory.objects.filter(is_active=True).prefetch_related('items')
        if not user.is_superuser and allowed_orgs.exists():
            categories_qs = categories_qs.filter(organization__in=allowed_orgs)

        overdue_deadlines = []
        upcoming_deadlines = []
        for category in categories_qs:
            for item in category.items.all():
                if item.next_date:
                    if item.next_date < today:
                        overdue_deadlines.append(item)
                    elif item.next_date <= warning_date:
                        upcoming_deadlines.append(item)

        # Медосмотры
        medical_qs = EmployeeMedicalExamination.objects.select_related('employee', 'harmful_factor')
        if not user.is_superuser and allowed_orgs.exists():
            medical_qs = medical_qs.filter(employee__organization__in=allowed_orgs)

        overdue_medical = []
        upcoming_medical = []
        for exam in medical_qs:
            if exam.next_date:
                if exam.next_date < today:
                    overdue_medical.append(exam)
                elif exam.next_date <= warning_date:
                    upcoming_medical.append(exam)

        # Передаём в контекст
        context.update({
            'total_equipment': equipment_qs.count(),
            'overdue_equipment': overdue_equipment,
            'overdue_equipment_count': len(overdue_equipment),
            'upcoming_equipment': upcoming_equipment,
            'upcoming_equipment_count': len(upcoming_equipment),

            'total_deadlines': sum(c.items.count() for c in categories_qs),
            'overdue_deadlines': overdue_deadlines,
            'overdue_deadlines_count': len(overdue_deadlines),
            'upcoming_deadlines': upcoming_deadlines,
            'upcoming_deadlines_count': len(upcoming_deadlines),

            'total_medical': medical_qs.count(),
            'overdue_medical': overdue_medical,
            'overdue_medical_count': len(overdue_medical),
            'upcoming_medical': upcoming_medical,
            'upcoming_medical_count': len(upcoming_medical),

            'total_overdue': len(overdue_equipment) + len(overdue_deadlines) + len(overdue_medical),
            'total_upcoming': len(upcoming_equipment) + len(upcoming_deadlines) + len(upcoming_medical),
        })

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


# Экспортируем все представления
__all__ = [
    'HomePageView',
    'IntroductoryBriefingView',
    'EmployeeListView',
    'EmployeeCreateView',
    'EmployeeUpdateView',
    'EmployeeDeleteView',
    'EmployeeHiringView',
    'EmployeeProfileView', # Добавляем в список экспорта
    'PositionListView',
    'PositionCreateView',
    'PositionUpdateView',
    'PositionDeleteView',
    'get_subdivisions',
    'get_positions',
    'get_departments',
    'UserRegistrationView',
    'DocumentSelectionView',
    'GeneratedDocumentListView',
    'document_download',
    'SIZIssueFormView',
    'SIZPersonalCardView',
    'SIZIssueReturnView',
    'employee_siz_issued_list',
]