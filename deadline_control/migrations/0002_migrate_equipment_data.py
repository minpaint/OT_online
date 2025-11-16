# Generated migration for data transfer from directory.Equipment to deadline_control.Equipment

from django.db import migrations


def migrate_equipment_data(apps, schema_editor):
    """
    Переносит данные из directory.Equipment в deadline_control.Equipment
    """
    # Получаем модели
    OldEquipment = apps.get_model('directory', 'Equipment')
    NewEquipment = apps.get_model('deadline_control', 'Equipment')

    # Переносим все записи
    for old_eq in OldEquipment.objects.all():
        NewEquipment.objects.create(
            id=old_eq.id,  # Сохраняем оригинальный ID
            equipment_name=old_eq.equipment_name,
            inventory_number=old_eq.inventory_number,
            organization=old_eq.organization,
            subdivision=old_eq.subdivision,
            department=old_eq.department,
            last_maintenance_date=old_eq.last_maintenance_date,
            next_maintenance_date=old_eq.next_maintenance_date,
            maintenance_period_months=old_eq.maintenance_period_months,
            maintenance_history=old_eq.maintenance_history,
            maintenance_status=old_eq.maintenance_status,
        )

    print(f"Перенесено {OldEquipment.objects.count()} записей Equipment")


def reverse_migrate_equipment_data(apps, schema_editor):
    """
    Обратная миграция - удаляет данные из новой таблицы
    """
    NewEquipment = apps.get_model('deadline_control', 'Equipment')
    count = NewEquipment.objects.count()
    NewEquipment.objects.all().delete()
    print(f"Удалено {count} записей Equipment из deadline_control")


class Migration(migrations.Migration):

    dependencies = [
        ('deadline_control', '0001_initial_models'),
        ('directory', '0038_add_siz_wear_type'),  # Последняя миграция directory
    ]

    operations = [
        migrations.RunPython(migrate_equipment_data, reverse_migrate_equipment_data),
    ]
