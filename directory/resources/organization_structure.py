"""
🏢 Resource для импорта/экспорта организационной структуры
Organization → StructuralSubdivision → Department → Position
"""
from import_export import resources, fields, widgets
from directory.models import Organization, StructuralSubdivision, Department, Position
from django.core.exceptions import ValidationError


class BooleanRussianWidget(widgets.BooleanWidget):
    """Виджет для обработки булевых значений на русском языке"""

    def clean(self, value, row=None, *args, **kwargs):
        if value in self.TRUE_VALUES:
            return True
        if value in self.FALSE_VALUES:
            return False

        # Обработка русских значений
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['да', 'yes', '1', 'true', 'т', 'y']:
                return True
            if value_lower in ['нет', 'no', '0', 'false', 'н', 'n', '']:
                return False

        return False


class OrganizationStructureResource(resources.ModelResource):
    """
    📊 Ресурс для импорта/экспорта организационной структуры.

    Простой подход: импортируем только поля Position,
    а organization/subdivision/department создаем в before_import_row.
    """

    class Meta:
        model = Position
        fields = (
            'organization',
            'subdivision',
            'department',
            'position_name',
            'safety_instructions_numbers',
            'internship_period_days',
            'is_responsible_for_safety',
            'can_be_internship_leader',
            'can_sign_orders',
        )
        import_id_fields = []
        skip_unchanged = False

    def before_import_row(self, row, **kwargs):
        """Создаем organization/subdivision/department перед импортом каждой строки"""

        # 1. Получаем данные из строки
        org_short_name = row.get('org_short_name_ru', '').strip() if row.get('org_short_name_ru') else ''
        subdivision_name = row.get('subdivision_name', '').strip() if row.get('subdivision_name') else ''
        department_name = row.get('department_name', '').strip() if row.get('department_name') else ''
        position_name = row.get('position_name', '').strip() if row.get('position_name') else ''

        # 2. Валидация
        if not org_short_name:
            raise ValidationError('Не указано краткое наименование организации')
        if not position_name:
            raise ValidationError('Не указано название должности')
        if department_name and not subdivision_name:
            raise ValidationError('Нельзя указать отдел без структурного подразделения')

        # 3. Создаем или находим организацию
        organization, _ = Organization.objects.get_or_create(
            short_name_ru=org_short_name,
            defaults={
                'full_name_ru': org_short_name,
                'short_name_by': org_short_name,
                'full_name_by': org_short_name,
                'location': 'г. Минск'
            }
        )

        # 4. Создаем или находим подразделение (если указано)
        subdivision = None
        if subdivision_name:
            subdivision, _ = StructuralSubdivision.objects.get_or_create(
                name=subdivision_name,
                organization=organization,
                defaults={'short_name': subdivision_name}
            )

        # 5. Создаем или находим отдел (если указан)
        department = None
        if department_name:
            department, _ = Department.objects.get_or_create(
                name=department_name,
                organization=organization,
                subdivision=subdivision,
                defaults={'short_name': department_name}
            )

        # 6. Добавляем ID в row для автоматического связывания
        row['organization'] = organization.id
        row['subdivision'] = subdivision.id if subdivision else None
        row['department'] = department.id if department else None

        # 7. Устанавливаем значения по умолчанию
        if row.get('internship_period_days') in (None, ''):
            row['internship_period_days'] = 0
        if row.get('is_responsible_for_safety') in (None, ''):
            row['is_responsible_for_safety'] = False
        if row.get('can_be_internship_leader') in (None, ''):
            row['can_be_internship_leader'] = False
        if row.get('can_sign_orders') in (None, ''):
            row['can_sign_orders'] = False

    def get_instance(self, instance_loader, row):
        """Ищем существующую должность или создаем новую"""
        org_id = row.get('organization')
        subdivision_id = row.get('subdivision')
        department_id = row.get('department')
        position_name = row.get('position_name')

        try:
            return Position.objects.get(
                position_name=position_name,
                organization_id=org_id,
                subdivision_id=subdivision_id,
                department_id=department_id
            )
        except Position.DoesNotExist:
            return None

    def get_export_queryset(self, queryset=None):
        """Оптимизация для экспорта"""
        qs = super().get_export_queryset(queryset)
        return qs.select_related('organization', 'subdivision', 'department')
