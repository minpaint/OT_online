# directory/migrations/0040_remove_old_medical_models.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0039_remove_old_equipment_model'),
        ('deadline_control', '0004_migrate_medical_data'),
    ]

    operations = [
        # Шаг 1: Обновляем ManyToManyField на Position
        migrations.AlterField(
            model_name='position',
            name='medical_harmful_factors',
            field=models.ManyToManyField(
                blank=True,
                related_name='positions',
                through='deadline_control.PositionMedicalFactor',
                to='deadline_control.harmfulfactor',
                verbose_name='Вредные факторы медосмотров'
            ),
        ),
        # Шаг 2: Удаляем старые модели (в обратном порядке зависимостей)
        migrations.DeleteModel(
            name='EmployeeMedicalExamination',
        ),
        migrations.DeleteModel(
            name='PositionMedicalFactor',
        ),
        migrations.DeleteModel(
            name='MedicalExaminationNorm',
        ),
        migrations.DeleteModel(
            name='HarmfulFactor',
        ),
        migrations.DeleteModel(
            name='MedicalSettings',
        ),
        migrations.DeleteModel(
            name='MedicalExaminationType',
        ),
    ]
