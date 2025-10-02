"""
👥 Resource для импорта/экспорта сотрудников
"""
from import_export import resources, fields, widgets
from directory.models import Employee, Organization, StructuralSubdivision, Department, Position
from django.core.exceptions import ValidationError
from datetime import datetime


class RussianDateWidget(widgets.DateWidget):
    """Виджет для обработки дат в формате DD.MM.YYYY"""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None

        # Если уже datetime
        if isinstance(value, datetime):
            return value.date()

        # Если date
        from datetime import date
        if isinstance(value, date):
            return value

        # Пробуем разные форматы (включая ISO формат из JSON)
        for fmt in ['%Y-%m-%dT%H:%M:%S', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except (ValueError, TypeError):
                continue

        return None


class EmployeeResource(resources.ModelResource):
    """
    👥 Ресурс для импорта/экспорта сотрудников.

    Простой подход: создаем organization/subdivision/department/position в before_import_row.
    """

    hire_date = fields.Field(
        column_name='hire_date',
        attribute='hire_date',
        widget=RussianDateWidget(format='%d.%m.%Y')
    )

    full_name_nominative = fields.Field(
        column_name='full_name_nominative',
        attribute='full_name_nominative',
        widget=widgets.CharWidget()
    )

    class Meta:
        model = Employee
        fields = (
            'organization',
            'subdivision',
            'department',
            'position',
            'hire_date',
            'full_name_nominative',
            'date_of_birth',
            'place_of_residence',
        )
        import_id_fields = []
        skip_unchanged = False

    def before_import_row(self, row, **kwargs):
        """Создаем organization/subdivision/department/position перед импортом каждой строки"""

        # 1. Получаем данные из строки
        org_short_name = row.get('org_short_name_ru', '').strip() if row.get('org_short_name_ru') else ''
        subdivision_name = row.get('subdivision_name', '').strip() if row.get('subdivision_name') else ''
        department_name = row.get('department_name', '').strip() if row.get('department_name') else ''
        position_name = row.get('position_name', '').strip() if row.get('position_name') else ''
        full_name = row.get('full_name_nominative', '').strip() if row.get('full_name_nominative') else ''

        # 2. Валидация
        if not org_short_name:
            raise ValidationError('Не указана организация')
        if not position_name:
            raise ValidationError('Не указана должность')
        if not full_name:
            raise ValidationError('Не указано ФИО сотрудника')
        if not row.get('hire_date'):
            raise ValidationError('Не указана дата приема')
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

        # 6. Создаем или находим должность
        position, _ = Position.objects.get_or_create(
            position_name=position_name,
            organization=organization,
            subdivision=subdivision,
            department=department,
            defaults={'position_name': position_name}
        )

        # 7. Добавляем ID в row для автоматического связывания
        row['organization'] = organization.id
        row['subdivision'] = subdivision.id if subdivision else None
        row['department'] = department.id if department else None
        row['position'] = position.id

        # 8. Устанавливаем значения по умолчанию для обязательных полей
        if not row.get('date_of_birth'):
            from datetime import date
            row['date_of_birth'] = date(1900, 1, 1)

        if not row.get('place_of_residence'):
            row['place_of_residence'] = 'Не указано'

    def after_import_row(self, row, row_result, **kwargs):
        """
        После импорта строки устанавливаем значения по умолчанию
        """
        if row_result.object_id:
            employee = Employee.objects.get(pk=row_result.object_id)

            # Автозаполнение полей по умолчанию
            # start_date должна быть равна hire_date
            if employee.hire_date:
                employee.start_date = employee.hire_date
            if not employee.contract_type:
                employee.contract_type = 'standard'
            if not employee.status:
                employee.status = 'active'

            employee.save()

    def get_instance(self, instance_loader, row):
        """Ищем существующего сотрудника по ФИО"""
        full_name = row.get('full_name_nominative')
        if full_name:
            try:
                return Employee.objects.get(full_name_nominative=full_name)
            except Employee.DoesNotExist:
                pass
        return None

    def get_export_queryset(self, queryset=None):
        """Оптимизация для экспорта"""
        qs = super().get_export_queryset(queryset)
        return qs.select_related('organization', 'subdivision', 'department', 'position')
