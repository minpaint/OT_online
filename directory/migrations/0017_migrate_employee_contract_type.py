# Generated manually

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0016_alter_equipment_maintenance_period_months'),  # Замените на вашу последнюю миграцию
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='contract_type',
            field=models.CharField(
                choices=[
                    ('standard', 'Трудовой договор'),
                    ('contractor', 'Договор подряда'),
                    ('part_time', 'Совмещение'),
                    ('transfer', 'Перевод'),
                    ('return', 'Выход из ДО')
                ],
                default='standard',
                max_length=20,
                verbose_name='Вид договора'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='hire_date',
            field=models.DateField(
                default=django.utils.timezone.now,
                verbose_name='Дата приема'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='start_date',
            field=models.DateField(
                default=django.utils.timezone.now,
                verbose_name='Дата начала работы'
            ),
        ),

        # Миграционные данные: заполняем contract_type на основе is_contractor
        migrations.RunPython(
            code=lambda apps, schema_editor:
            apps.get_model('directory', 'Employee').objects.filter(is_contractor=True).update(
                contract_type='contractor'),
            reverse_code=lambda apps, schema_editor:
            apps.get_model('directory', 'Employee').objects.filter(contract_type='contractor').update(
                is_contractor=True)
        ),
    ]