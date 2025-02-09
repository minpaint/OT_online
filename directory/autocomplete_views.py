from dal import autocomplete
from django.db.models import Q
from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Position,
    Document,
    Equipment
)


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    """
    🏢 Автодополнение для организаций
    """

    def get_queryset(self):
        qs = Organization.objects.all()
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
        qs = StructuralSubdivision.objects.all()

        # Получаем id организации из forwarded параметров
        organization = self.forwarded.get('organization', None)
        if organization:
            qs = qs.filter(organization_id=organization)
        else:
            return StructuralSubdivision.objects.none()

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
        qs = Department.objects.all()

        # Получаем id подразделения из forwarded параметров
        subdivision = self.forwarded.get('subdivision', None)
        if subdivision:
            qs = qs.filter(subdivision_id=subdivision)
        else:
            return Department.objects.none()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(short_name__icontains=self.q)
            )
        return qs.select_related('subdivision', 'organization').order_by('name')

    def get_result_label(self, item):
        return f"{item.name} ({item.subdivision.name})"


class PositionAutocomplete(autocomplete.Select2QuerySetView):
    """
    👔 Автодополнение для должностей
    """

    def get_queryset(self):
        qs = Position.objects.all()

        # Получаем параметры из forwarded
        organization = self.forwarded.get('organization', None)
        subdivision = self.forwarded.get('subdivision', None)
        department = self.forwarded.get('department', None)

        # Базовая фильтрация по организации
        if organization:
            qs = qs.filter(organization_id=organization)
        else:
            return Position.objects.none()

        # Дополнительные фильтры
        if department:
            # Если указан отдел, ищем должности этого отдела
            qs = qs.filter(department_id=department)
        elif subdivision:
            # Если указано только подразделение, ищем должности этого подразделения
            # или должности без отдела
            qs = qs.filter(
                Q(subdivision_id=subdivision, department__isnull=True) |
                Q(subdivision_id=subdivision)
            )
        else:
            # Если указана только организация, ищем должности без подразделения
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

    Поиск документов с учетом организационной структуры.
    Поддерживает фильтрацию по:
    - организации
    - подразделению
    - отделу
    """

    def get_queryset(self):
        qs = Document.objects.all()

        # Получаем параметры из forwarded
        organization = self.forwarded.get('organization', None)
        subdivision = self.forwarded.get('subdivision', None)
        department = self.forwarded.get('department', None)

        # Базовая фильтрация по организации
        if organization:
            qs = qs.filter(organization_id=organization)
        else:
            return Document.objects.none()

        # Фильтрация по подразделению и отделу
        if department:
            # Если указан отдел, ищем документы этого отдела
            qs = qs.filter(department_id=department)
        elif subdivision:
            # Если указано подразделение, ищем документы этого подразделения
            # или документы без отдела
            qs = qs.filter(
                Q(subdivision_id=subdivision, department__isnull=True) |
                Q(subdivision_id=subdivision)
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
        """Формирование отображаемого названия документа"""
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

    Поиск оборудования с учетом организационной структуры.
    Поддерживает фильтрацию по:
    - организации
    - подразделению
    - отделу
    """

    def get_queryset(self):
        qs = Equipment.objects.all()

        # Получаем параметры из forwarded
        organization = self.forwarded.get('organization', None)
        subdivision = self.forwarded.get('subdivision', None)
        department = self.forwarded.get('department', None)

        # Базовая фильтрация по организации
        if organization:
            qs = qs.filter(organization_id=organization)
        else:
            return Equipment.objects.none()

        # Фильтрация по подразделению и отделу
        if department:
            # Если указан отдел, ищем оборудование этого отдела
            qs = qs.filter(department_id=department)
        elif subdivision:
            # Если указано подразделение, ищем оборудование этого подразделения
            # или оборудование без отдела
            qs = qs.filter(
                Q(subdivision_id=subdivision, department__isnull=True) |
                Q(subdivision_id=subdivision)
            )

        # Поиск по названию и инвентарному номеру
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
        """Формирование отображаемого названия оборудования"""
        parts = [f"{item.equipment_name} (инв.№ {item.inventory_number})"]

        if item.department:
            parts.append(f"- {item.department.name}")
        elif item.subdivision:
            parts.append(f"- {item.subdivision.name}")
        else:
            parts.append(f"- {item.organization.short_name_ru}")

        return " ".join(parts)