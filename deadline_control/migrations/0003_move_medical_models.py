# deadline_control/migrations/0003_move_medical_models.py
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('deadline_control', '0002_migrate_equipment_data'),
        ('directory', '0039_remove_old_equipment_model'),
    ]

    operations = [
        # Шаг 1: Создаем новые таблицы в deadline_control
        migrations.CreateModel(
            name='MedicalExaminationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Название типа медосмотра', max_length=100, unique=True, verbose_name='Название типа')),
                ('description', models.TextField(blank=True, help_text='Описание типа медосмотра', verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Тип медосмотра',
                'verbose_name_plural': 'Типы медосмотров',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MedicalSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days_before_warning', models.PositiveIntegerField(default=30, help_text='За сколько дней до истечения срока показывать предупреждение', verbose_name='Дней до предупреждения')),
            ],
            options={
                'verbose_name': 'Настройки медосмотров',
                'verbose_name_plural': 'Настройки медосмотров',
            },
        ),
        migrations.CreateModel(
            name='HarmfulFactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(db_index=True, help_text='Краткое название фактора', max_length=100, verbose_name='Краткое наименование')),
                ('full_name', models.CharField(help_text='Полное официальное название фактора', max_length=500, verbose_name='Полное наименование')),
                ('periodicity', models.PositiveIntegerField(default=12, help_text='Периодичность медосмотров в месяцах', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Периодичность (месяцы)')),
            ],
            options={
                'verbose_name': 'Вредный фактор',
                'verbose_name_plural': 'Вредные факторы',
                'ordering': ['short_name'],
                'unique_together': {('short_name', 'periodicity')},
            },
        ),
        migrations.CreateModel(
            name='MedicalExaminationNorm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_name', models.CharField(db_index=True, help_text='Название должности, для которой определяется норма медосмотра', max_length=255, verbose_name='Наименование должности')),
                ('periodicity_override', models.PositiveIntegerField(blank=True, help_text='Если указано, переопределяет периодичность медосмотра (в месяцах)', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Переопределение периодичности (месяцы)')),
                ('notes', models.TextField(blank=True, help_text='Дополнительная информация о норме', verbose_name='Примечания')),
                ('harmful_factor', models.ForeignKey(help_text='Вредный фактор, определяющий необходимость прохождения медосмотра', on_delete=django.db.models.deletion.CASCADE, related_name='medical_norms', to='deadline_control.harmfulfactor', verbose_name='Вредный фактор')),
            ],
            options={
                'verbose_name': 'Норма медосмотра',
                'verbose_name_plural': 'Нормы медосмотров',
                'ordering': ['position_name', 'harmful_factor'],
                'unique_together': {('position_name', 'harmful_factor')},
            },
        ),
        migrations.CreateModel(
            name='PositionMedicalFactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periodicity_override', models.PositiveIntegerField(blank=True, help_text='Если указано, переопределяет периодичность медосмотра (в месяцах)', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Переопределение периодичности (месяцы)')),
                ('is_disabled', models.BooleanField(default=False, help_text='Если отмечено, фактор не применяется для данной должности', verbose_name='Отключено')),
                ('notes', models.TextField(blank=True, help_text='Дополнительная информация о применении фактора к должности', verbose_name='Примечания')),
                ('harmful_factor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position_factors', to='deadline_control.harmfulfactor', verbose_name='Вредный фактор')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_factors', to='directory.position', verbose_name='Должность')),
            ],
            options={
                'verbose_name': 'Вредный фактор должности',
                'verbose_name_plural': 'Вредные факторы должностей',
                'ordering': ['position', 'harmful_factor'],
                'unique_together': {('position', 'harmful_factor')},
            },
        ),
        migrations.CreateModel(
            name='EmployeeMedicalExamination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_completed', models.DateField(help_text='Дата фактического прохождения медосмотра', verbose_name='Дата прохождения')),
                ('next_date', models.DateField(help_text='Плановая дата следующего медосмотра', verbose_name='Дата следующего медосмотра')),
                ('medical_certificate', models.FileField(blank=True, null=True, upload_to='medical_certificates/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name='Скан справки')),
                ('status', models.CharField(choices=[('completed', 'Пройден'), ('expired', 'Просрочен'), ('scheduled', 'Запланирован'), ('to_issue', 'Нужно выдать направление')], default='completed', help_text='Текущий статус медосмотра', max_length=20, verbose_name='Статус')),
                ('notes', models.TextField(blank=True, help_text='Дополнительная информация о медосмотре', verbose_name='Примечания')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления записи')),
                ('employee', models.ForeignKey(help_text='Сотрудник, для которого регистрируется медосмотр', on_delete=django.db.models.deletion.CASCADE, related_name='medical_examinations', to='directory.employee', verbose_name='Сотрудник')),
                ('harmful_factor', models.ForeignKey(help_text='Вредный фактор, по которому проводился медосмотр', on_delete=django.db.models.deletion.PROTECT, related_name='employee_examinations', to='deadline_control.harmfulfactor', verbose_name='Вредный фактор')),
            ],
            options={
                'verbose_name': 'Медосмотр сотрудника',
                'verbose_name_plural': 'Медосмотры сотрудников',
                'ordering': ['-date_completed', 'employee'],
            },
        ),
    ]
