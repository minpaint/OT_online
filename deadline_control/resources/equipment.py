"""
⚙️ Resource для импорта/экспорта оборудования
"""
from import_export import resources, fields
from import_export.widgets import CharWidget, DateWidget
from deadline_control.models import Equipment
from directory.models import Organization, StructuralSubdivision, Department
from django.core.exceptions import ValidationError
from datetime import datetime


class RussianDateWidget(DateWidget):
    """Виджет для обработки дат в формате DD.MM.YYYY"""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None

        # Если уже datetime
        if isinstance(value, datetime):
            return value.date()

        # Пробуем разные форматы
        for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except (ValueError, TypeError):
                continue

        return None


class EquipmentResource(resources.ModelResource):
    """
    ⚙️ Ресурс для импорта/экспорта оборудования.

    Автоматически:
    - Создает Organization/Subdivision/Department при отсутствии
    - Генерирует инвентарный номер (8 цифр) если не указан
    - Рассчитывает next_maintenance_date
    - Обновляет существующее оборудование по inventory_number

    Структура файла (7 столбцов):
    1. org_short_name_ru - краткое наименование организации (обязательное)
    2. subdivision_name - структурное подразделение (опционально)
    3. department_name - отдел (опционально)
    4. equipment_name - наименование оборудования (обязательное)
    5. inventory_number - инвентарный номер (опционально, автогенерация)
    6. maintenance_period_months - периодичность ТО в месяцах (опционально)
    7. last_maintenance_date - дата последнего ТО (опционально)
    """

    # Поля организационной структуры
    org_short_name_ru = fields.Field(
        column_name='org_short_name_ru',
        attribute='organization__short_name_ru',
        widget=CharWidget()
    )

    subdivision_name = fields.Field(
        column_name='subdivision_name',
        attribute='subdivision__name',
        widget=CharWidget()
    )

    department_name = fields.Field(
        column_name='department_name',
        attribute='department__name',
        widget=CharWidget()
    )

    # Поля оборудования
    equipment_name = fields.Field(
        column_name='equipment_name',
        attribute='equipment_name',
        widget=CharWidget()
    )

    inventory_number = fields.Field(
        column_name='inventory_number',
        attribute='inventory_number',
        widget=CharWidget()
    )

    maintenance_period_months = fields.Field(
        column_name='maintenance_period_months',
        attribute='maintenance_period_months'
    )

    last_maintenance_date = fields.Field(
        column_name='last_maintenance_date',
        attribute='last_maintenance_date',
        widget=RussianDateWidget(format='%d.%m.%Y')
    )

    class Meta:
        model = Equipment
        fields = (
            'org_short_name_ru',
            'subdivision_name',
            'department_name',
            'equipment_name',
            'inventory_number',
            'maintenance_period_months',
            'last_maintenance_date'
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        import_id_fields = []

    def before_import_row(self, row, **kwargs):
        """Валидация строки перед импортом"""
        errors = []

        # Проверка обязательных полей
        if not row.get('org_short_name_ru'):
            errors.append('Не указана организация (org_short_name_ru)')
        if not row.get('equipment_name'):
            errors.append('Не указано наименование оборудования (equipment_name)')

        # Валидация иерархии
        if row.get('department_name') and not row.get('subdivision_name'):
            errors.append('Нельзя указать отдел без структурного подразделения')

        if errors:
            raise ValidationError('; '.join(errors))

    def _generate_inventory_number(self):
        """Генерирует уникальный инвентарный номер из 8 цифр"""
        last_equipment = Equipment.objects.filter(
            inventory_number__regex=r'^\d{8}$'
        ).order_by('inventory_number').last()

        if last_equipment:
            try:
                last_number = int(last_equipment.inventory_number)
                new_number = last_number + 1
            except (ValueError, TypeError):
                new_number = 1
        else:
            new_number = 1

        return f"{new_number:08d}"

    def import_obj(self, obj, data, dry_run, **kwargs):
        """
        Переопределяем метод импорта для:
        1. Каскадного создания Organization → Subdivision → Department
        2. Автогенерации инвентарного номера
        3. Расчета next_maintenance_date
        4. Обновления существующего оборудования
        """

        # 1. Создаем или получаем Organization
        org_short_name = data.get('org_short_name_ru', '').strip()

        if not dry_run:
            organization, created = Organization.objects.get_or_create(
                short_name_ru=org_short_name,
                defaults={
                    'short_name_ru': org_short_name,
                    'full_name_ru': org_short_name,
                    'short_name_by': org_short_name,
                    'full_name_by': org_short_name,
                    'location': 'г. Минск'
                }
            )
        else:
            try:
                organization = Organization.objects.get(short_name_ru=org_short_name)
            except Organization.DoesNotExist:
                organization = Organization(short_name_ru=org_short_name, full_name_ru=org_short_name)

        obj.organization = organization

        # 2. Создаем или получаем StructuralSubdivision (если указано)
        subdivision_name = data.get('subdivision_name', '').strip()
        if subdivision_name:
            subdivision_data = {
                'name': subdivision_name,
                'short_name': subdivision_name,
                'organization': organization
            }

            if not dry_run:
                subdivision, created = StructuralSubdivision.objects.get_or_create(
                    name=subdivision_name,
                    organization=organization,
                    defaults=subdivision_data
                )
            else:
                try:
                    subdivision = StructuralSubdivision.objects.get(
                        name=subdivision_name,
                        organization=organization
                    )
                except StructuralSubdivision.DoesNotExist:
                    subdivision = StructuralSubdivision(**subdivision_data)

            obj.subdivision = subdivision
        else:
            obj.subdivision = None

        # 3. Создаем или получаем Department (если указано)
        department_name = data.get('department_name', '').strip()
        if department_name:
            department_data = {
                'name': department_name,
                'short_name': department_name,
                'organization': organization,
                'subdivision': obj.subdivision
            }

            if not dry_run:
                department, created = Department.objects.get_or_create(
                    name=department_name,
                    organization=organization,
                    subdivision=obj.subdivision,
                    defaults=department_data
                )
            else:
                try:
                    department = Department.objects.get(
                        name=department_name,
                        organization=organization,
                        subdivision=obj.subdivision
                    )
                except Department.DoesNotExist:
                    department = Department(**department_data)

            obj.department = department
        else:
            obj.department = None

        # 4. Заполняем поля оборудования
        obj.equipment_name = data.get('equipment_name', '').strip()

        # Инвентарный номер - автогенерация если пустой
        inventory_number = data.get('inventory_number', '').strip()
        if not inventory_number:
            if not dry_run:
                inventory_number = self._generate_inventory_number()
            else:
                inventory_number = "00000000"  # Заглушка для предпросмотра

        obj.inventory_number = inventory_number

        # Периодичность ТО - если пустое, остается NULL
        maintenance_period = data.get('maintenance_period_months', '')
        if maintenance_period:
            try:
                obj.maintenance_period_months = int(maintenance_period)
            except (ValueError, TypeError):
                obj.maintenance_period_months = None
        else:
            obj.maintenance_period_months = None

        # Дата последнего ТО
        obj.last_maintenance_date = data.get('last_maintenance_date')

        # Рассчитываем дату следующего ТО только если указаны оба поля
        if obj.last_maintenance_date and obj.maintenance_period_months:
            obj.next_maintenance_date = Equipment._add_months(
                obj.last_maintenance_date,
                obj.maintenance_period_months
            )
        else:
            obj.next_maintenance_date = None

        # Статус по умолчанию - исправно
        obj.maintenance_status = 'operational'

        # 5. Проверяем, существует ли оборудование с таким инвентарным номером
        if not dry_run:
            existing_equipment = Equipment.objects.filter(
                inventory_number=obj.inventory_number
            ).first()

            if existing_equipment:
                # Обновляем существующее оборудование
                obj.id = existing_equipment.id

        return obj

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Не пропускаем строки - всегда создаем или обновляем"""
        return False

    def get_export_queryset(self, queryset=None):
        """Оптимизируем запрос для экспорта"""
        qs = super().get_export_queryset(queryset)
        return qs.select_related('organization', 'subdivision', 'department')
