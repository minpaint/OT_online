# deadline_control/migrations/0004_migrate_medical_data.py
from django.db import migrations


def migrate_medical_data(apps, schema_editor):
    """Переносим данные из directory в deadline_control"""

    # Старые модели из directory
    OldMedicalExaminationType = apps.get_model('directory', 'MedicalExaminationType')
    OldMedicalSettings = apps.get_model('directory', 'MedicalSettings')
    OldHarmfulFactor = apps.get_model('directory', 'HarmfulFactor')
    OldMedicalExaminationNorm = apps.get_model('directory', 'MedicalExaminationNorm')
    OldPositionMedicalFactor = apps.get_model('directory', 'PositionMedicalFactor')
    OldEmployeeMedicalExamination = apps.get_model('directory', 'EmployeeMedicalExamination')

    # Новые модели в deadline_control
    NewMedicalExaminationType = apps.get_model('deadline_control', 'MedicalExaminationType')
    NewMedicalSettings = apps.get_model('deadline_control', 'MedicalSettings')
    NewHarmfulFactor = apps.get_model('deadline_control', 'HarmfulFactor')
    NewMedicalExaminationNorm = apps.get_model('deadline_control', 'MedicalExaminationNorm')
    NewPositionMedicalFactor = apps.get_model('deadline_control', 'PositionMedicalFactor')
    NewEmployeeMedicalExamination = apps.get_model('deadline_control', 'EmployeeMedicalExamination')

    # Маппинг старых ID на новые объекты
    harmful_factor_map = {}

    # 1. Переносим MedicalExaminationType
    for old in OldMedicalExaminationType.objects.all():
        NewMedicalExaminationType.objects.create(
            id=old.id,
            name=old.name,
            description=getattr(old, 'description', '')
        )

    # 2. Переносим MedicalSettings
    for old in OldMedicalSettings.objects.all():
        NewMedicalSettings.objects.create(
            id=old.id,
            days_before_warning=old.days_before_warning
        )

    # 3. Переносим HarmfulFactor
    for old in OldHarmfulFactor.objects.all():
        new_factor = NewHarmfulFactor.objects.create(
            id=old.id,
            short_name=old.short_name,
            full_name=old.full_name,
            periodicity=old.periodicity
        )
        harmful_factor_map[old.id] = new_factor

    # 4. Переносим MedicalExaminationNorm
    for old in OldMedicalExaminationNorm.objects.all():
        NewMedicalExaminationNorm.objects.create(
            id=old.id,
            position_name=old.position_name,
            harmful_factor=harmful_factor_map[old.harmful_factor_id],
            periodicity_override=old.periodicity_override,
            notes=old.notes
        )

    # 5. Переносим PositionMedicalFactor
    for old in OldPositionMedicalFactor.objects.all():
        NewPositionMedicalFactor.objects.create(
            id=old.id,
            position_id=old.position_id,
            harmful_factor=harmful_factor_map[old.harmful_factor_id],
            periodicity_override=old.periodicity_override,
            is_disabled=old.is_disabled,
            notes=old.notes
        )

    # 6. Переносим EmployeeMedicalExamination
    for old in OldEmployeeMedicalExamination.objects.all():
        NewEmployeeMedicalExamination.objects.create(
            id=old.id,
            employee_id=old.employee_id,
            harmful_factor=harmful_factor_map[old.harmful_factor_id],
            date_completed=old.date_completed,
            next_date=old.next_date,
            medical_certificate=old.medical_certificate,
            status=old.status,
            notes=old.notes,
        )


def reverse_migrate_medical_data(apps, schema_editor):
    """Откат миграции - не реализован"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('deadline_control', '0003_move_medical_models'),
        ('directory', '0039_remove_old_equipment_model'),
    ]

    operations = [
        migrations.RunPython(migrate_medical_data, reverse_migrate_medical_data),
    ]
