from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from directory.models import Employee
from directory.utils.permissions import AccessControlHelper


class Command(BaseCommand):
    help = 'Отладка системы прав доступа'

    def handle(self, *args, **options):
        # Проверяем workshop_manager
        try:
            user = User.objects.get(username='workshop_manager')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь workshop_manager не найден'))
            return

        self.stdout.write("=" * 80)
        self.stdout.write(f"Пользователь: {user.username}")
        self.stdout.write("=" * 80)

        # Проверяем профиль
        if not hasattr(user, 'profile'):
            self.stdout.write(self.style.ERROR('У пользователя нет профиля!'))
            return

        profile = user.profile

        self.stdout.write(f"\nПрофиль:")
        self.stdout.write(f"  - organizations: {list(profile.organizations.all())}")
        self.stdout.write(f"  - subdivisions: {list(profile.subdivisions.all())}")
        self.stdout.write(f"  - departments: {list(profile.departments.all())}")

        # Проверяем методы AccessControlHelper
        orgs = AccessControlHelper.get_accessible_organizations(user)
        subdivs = AccessControlHelper.get_accessible_subdivisions(user)
        depts = AccessControlHelper.get_accessible_departments(user)

        self.stdout.write(f"\nДоступные объекты:")
        self.stdout.write(f"  - organizations: {list(orgs)}")
        self.stdout.write(f"  - subdivisions: {list(subdivs)}")
        self.stdout.write(f"  - departments: {list(depts)}")

        # Проверяем фильтрацию Employee
        all_employees = Employee.objects.all()
        self.stdout.write(f"\nВсего сотрудников в БД: {all_employees.count()}")
        for emp in all_employees:
            self.stdout.write(f"  - {emp.full_name_nominative}: org={emp.organization}, subdiv={emp.subdivision}, dept={emp.department}")

        # Фильтруем
        filtered = AccessControlHelper.filter_queryset(all_employees, user)
        self.stdout.write(f"\nОтфильтровано сотрудников: {filtered.count()}")
        for emp in filtered:
            self.stdout.write(f"  - {emp.full_name_nominative}: org={emp.organization}, subdiv={emp.subdivision}, dept={emp.department}")

        # Проверяем поля модели
        field_names = [f.name for f in Employee._meta.get_fields()]
        self.stdout.write(f"\nПоля модели Employee:")
        self.stdout.write(f"  - organization: {'organization' in field_names}")
        self.stdout.write(f"  - subdivision: {'subdivision' in field_names}")
        self.stdout.write(f"  - department: {'department' in field_names}")

        # Проверяем SQL запрос
        self.stdout.write(f"\nSQL запрос:")
        self.stdout.write(str(filtered.query))
