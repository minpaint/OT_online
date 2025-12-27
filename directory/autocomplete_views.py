from dal import autocomplete
from django.db.models import Q
from directory.models.siz import SIZ
from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Position,
    Document,
    Employee,
    Commission
)
from deadline_control.models import Equipment


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    """
    🏢 Автодополнение для организаций
    """
    def get_queryset(self):
        # Если пользователь не залогинен, возвращаем пустой набор
        if not self.request.user.is_authenticated:
            return Organization.objects.none()

        qs = Organization.objects.all()

        # 🔒 Если не суперпользователь, фильтруем по организациям из профиля
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(pk__in=allowed_orgs)

        # Поиск по названию
        if self.q:
            qs = qs.filter(
                Q(full_name_ru__icontains=self.q) |
                Q(short_name_ru__icontains=self.q)
            )

        return qs.order_by('full_name_ru')

    def get_result_label(self, item):
        return item.short_name_ru or item.full_name_ru


class SubdivisionAutocomplete(autocomplete.Select2QuerySetView):
    """
    🏭 Автодополнение для подразделений
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return StructuralSubdivision.objects.none()

        qs = StructuralSubdivision.objects.all()

        # 🔒 Фильтруем по профилю, если не суперпользователь
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Из forwarded-параметров получаем id организации
        organization_id = self.forwarded.get('organization', None)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        else:
            return StructuralSubdivision.objects.none()

        # Поиск по названию
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(short_name__icontains=self.q)
            )

        return qs.select_related('organization').order_by('name')

    def get_result_label(self, item):
        return f"{item.name} ({item.organization.short_name_ru})"


class DepartmentAutocomplete(autocomplete.Select2QuerySetView):
    """
    📂 Автодополнение для отделов
    """

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Department.objects.none()

        qs = Department.objects.all()

        # 🔒 Фильтрация по профилю
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Получаем параметры из forwarded
        subdivision_id = self.forwarded.get('subdivision', None)
        organization_id = self.forwarded.get('organization', None)

        # Создаем фильтр для согласованной фильтрации
        if subdivision_id:
            qs = qs.filter(subdivision_id=subdivision_id)

            # Дополнительно проверяем согласованность с организацией
            if organization_id:
                qs = qs.filter(organization_id=organization_id)
        else:
            # Если подразделение не выбрано, возвращаем пустой результат
            return Department.objects.none()

        # Поиск по названию
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(short_name__icontains=self.q)
            )

        return qs.select_related('subdivision', 'organization').order_by('name')

    def get_result_label(self, item):
        return (
            f"{item.name} ({item.subdivision.name})"
            if item.subdivision else item.name
        )


class PositionAutocomplete(autocomplete.Select2QuerySetView):
    """
    👔 Автодополнение для должностей
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Position.objects.none()

        qs = Position.objects.all()

        # 🔒 Фильтрация по профилю
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Читаем forwarded: organization, subdivision, department
        organization_id = self.forwarded.get('organization', None)
        subdivision_id = self.forwarded.get('subdivision', None)
        department_id = self.forwarded.get('department', None)

        # Базовая фильтрация по организации
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        else:
            return Position.objects.none()

        # Дополнительная логика
        if department_id:
            qs = qs.filter(department_id=department_id)
        elif subdivision_id:
            qs = qs.filter(
                Q(subdivision_id=subdivision_id, department__isnull=True) |
                Q(subdivision_id=subdivision_id)
            )
        else:
            qs = qs.filter(subdivision__isnull=True)

        if self.q:
            qs = qs.filter(position_name__icontains=self.q)

        return qs.select_related(
            'organization',
            'subdivision',
            'department'
        ).order_by('position_name')

    def get_result_label(self, item):
        parts = [item.position_name]
        if item.department:
            parts.append(f"({item.department.name})")
        elif item.subdivision:
            parts.append(f"({item.subdivision.name})")
        else:
            parts.append(f"({item.organization.short_name_ru})")
        return " ".join(parts)


class DocumentAutocomplete(autocomplete.Select2QuerySetView):
    """
    📄 Автодополнение для документов
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Document.objects.none()

        qs = Document.objects.all()

        # 🔒 Фильтрация по профилю
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Считываем forwarded
        organization_id = self.forwarded.get('organization', None)
        subdivision_id = self.forwarded.get('subdivision', None)
        department_id = self.forwarded.get('department', None)

        # Базовая фильтрация по организации
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        else:
            return Document.objects.none()

        # Дополнительная фильтрация по subdivision / department
        if department_id:
            qs = qs.filter(department_id=department_id)
        elif subdivision_id:
            qs = qs.filter(
                Q(subdivision_id=subdivision_id, department__isnull=True) |
                Q(subdivision_id=subdivision_id)
            )

        # Поиск по названию документа
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.select_related(
            'organization',
            'subdivision',
            'department'
        ).order_by('name')

    def get_result_label(self, item):
        parts = [item.name]
        if item.department:
            parts.append(f"({item.department.name})")
        elif item.subdivision:
            parts.append(f"({item.subdivision.name})")
        else:
            parts.append(f"({item.organization.short_name_ru})")
        return " ".join(parts)


class EquipmentAutocomplete(autocomplete.Select2QuerySetView):
    """
    ⚙️ Автодополнение для оборудования
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Equipment.objects.none()

        qs = Equipment.objects.all()

        # 🔒 Фильтрация по профилю
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Считываем forwarded
        organization_id = self.forwarded.get('organization', None)
        subdivision_id = self.forwarded.get('subdivision', None)
        department_id = self.forwarded.get('department', None)

        # Базовая фильтрация по organization
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        else:
            return Equipment.objects.none()

        # Дополнительная фильтрация
        if department_id:
            qs = qs.filter(department_id=department_id)
        elif subdivision_id:
            qs = qs.filter(
                Q(subdivision_id=subdivision_id, department__isnull=True) |
                Q(subdivision_id=subdivision_id)
            )

        # Поиск по названию/инв. номеру
        if self.q:
            qs = qs.filter(
                Q(equipment_name__icontains=self.q) |
                Q(inventory_number__icontains=self.q)
            )

        return qs.select_related(
            'organization',
            'subdivision',
            'department'
        ).order_by('equipment_name')

    def get_result_label(self, item):
        parts = [f"{item.equipment_name} (инв.№ {item.inventory_number})"]
        if item.department:
            parts.append(f"- {item.department.name}")
        elif item.subdivision:
            parts.append(f"- {item.subdivision.name}")
        else:
            parts.append(f"- {item.organization.short_name_ru}")
        return " ".join(parts)


class SIZAutocomplete(autocomplete.Select2QuerySetView):
    """
    🛡️ Автодополнение для выбора СИЗ
    Используется в формах для удобного выбора СИЗ из списка
    """
    def get_queryset(self):
        """
        🔍 Получение отфильтрованного набора СИЗ
        на основе поискового запроса
        """
        from django.db.models import Q

        if not self.request.user.is_authenticated:
            return SIZ.objects.none()

        qs = SIZ.objects.all()

        if self.q:
            # Используем Q-объекты для поиска с учетом регистра и без
            # Это решает проблему с SQLite, где icontains не всегда работает корректно
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(name__icontains=self.q.capitalize()) |
                Q(name__icontains=self.q.lower()) |
                Q(name__icontains=self.q.upper())
            ).distinct()

        return qs.order_by('name')


class EmployeeByCommissionAutocomplete(autocomplete.Select2QuerySetView):
    """
    Автодополнение для выбора сотрудников, фильтрующее по организационной структуре комиссии
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Employee.objects.none()

        qs = Employee.objects.filter(is_active=True)

        # Получаем id комиссии из параметра forward
        commission_id = self.forwarded.get('commission', None)
        if commission_id:
            try:
                commission = Commission.objects.get(id=commission_id)

                # Фильтруем сотрудников в зависимости от привязки комиссии
                if commission.department:
                    qs = qs.filter(department=commission.department)
                elif commission.subdivision:
                    qs = qs.filter(subdivision=commission.subdivision)
                elif commission.organization:
                    qs = qs.filter(organization=commission.organization)
            except Commission.DoesNotExist:
                pass

        if self.q:
            qs = qs.filter(
                Q(full_name_nominative__icontains=self.q)
            )

        return qs.select_related('position', 'organization', 'subdivision', 'department').order_by('full_name_nominative')

    def get_result_label(self, result):
        position = result.position.position_name if result.position else "Без должности"
        return f"{result.full_name_nominative} - {position}"


class EmployeeForCommissionAutocomplete(autocomplete.Select2QuerySetView):
    """
    👤 Автодополнение для выбора сотрудников в комиссию с учетом иерархии
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Employee.objects.none()

        # Получаем доступные организации через AccessControlHelper
        from directory.utils.permissions import AccessControlHelper
        accessible_orgs = AccessControlHelper.get_accessible_organizations(
            self.request.user, self.request
        )

        # Базовый queryset с фильтрацией по доступным организациям
        qs = Employee.objects.filter(organization__in=accessible_orgs)

        # Получаем параметры из forwarded (для использования в комиссиях)
        organization_id = self.forwarded.get('organization', None)
        subdivision_id = self.forwarded.get('subdivision', None)
        department_id = self.forwarded.get('department', None)
        commission_id = self.forwarded.get('commission', None)

        # Если передан ID комиссии, используем его для определения структуры
        if commission_id:
            try:
                commission = Commission.objects.get(id=commission_id)
                if commission.department:
                    department_id = commission.department.id
                    subdivision_id = commission.department.subdivision_id
                    organization_id = commission.department.organization_id
                elif commission.subdivision:
                    subdivision_id = commission.subdivision.id
                    organization_id = commission.subdivision.organization_id
                elif commission.organization:
                    organization_id = commission.organization.id
            except Commission.DoesNotExist:
                pass

        # Фильтруем по иерархии (если параметры переданы)
        if department_id:
            qs = qs.filter(position__department_id=department_id)
        elif subdivision_id:
            qs = qs.filter(position__department__subdivision_id=subdivision_id)
        elif organization_id:
            qs = qs.filter(organization_id=organization_id)
        # Иначе показываем всех сотрудников из доступных организаций

        # Поиск по ФИО
        if self.q:
            qs = qs.filter(
                Q(full_name_nominative__icontains=self.q)
            )

        return qs.select_related(
            'position',
            'organization',
            'position__department',
            'position__department__subdivision'
        ).order_by('full_name_nominative')

    def get_result_label(self, item):
        # Форматируем результат для отображения
        position = item.position.position_name if item.position else "Нет должности"
        return f"{item.full_name_nominative} - {position}"


class CommissionAutocomplete(autocomplete.Select2QuerySetView):
    """
    Автодополнение для выбора комиссий
    """
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Commission.objects.none()

        qs = Commission.objects.all()

        # Фильтрация по активности
        qs = qs.filter(is_active=True)

        # Фильтрация по организациям пользователя
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(
                Q(organization__in=allowed_orgs) |
                Q(subdivision__organization__in=allowed_orgs) |
                Q(department__organization__in=allowed_orgs)
            )

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('name')

    def get_result_label(self, item):
        # Форматируем результат с учетом уровня
        if item.department:
            return f"{item.name} ({item.department.name})"
        elif item.subdivision:
            return f"{item.name} ({item.subdivision.name})"
        elif item.organization:
            return f"{item.name} ({item.organization.short_name_ru})"
        return item.name