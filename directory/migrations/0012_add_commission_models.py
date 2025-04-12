# directory/migrations/XXXX_add_commission_models.py
# Создается автоматически с помощью команды `python manage.py makemigrations`
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0011_alter_documenttemplate_document_type_and_more'),  # Замените на фактическую предыдущую миграцию
    ]
    operations = [
        # Сначала удаляем поле commission_role из модели Position
        migrations.RemoveField(
            model_name='position',
            name='commission_role',
        ),

        # Затем создаем новые модели
        migrations.CreateModel(
            name='Commission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование комиссии')),
                ('commission_type', models.CharField(
                    choices=[('ot', '🛡️ Охрана труда'), ('eb', '⚡ Электробезопасность'),
                             ('pb', '🔥 Пожарная безопасность'), ('other', '📋 Иная')], default='ot', max_length=10,
                    verbose_name='Тип комиссии')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name='commissions', to='directory.Department',
                                                 verbose_name='Отдел')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                   related_name='commissions', to='directory.Organization',
                                                   verbose_name='Организация')),
                ('subdivision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                  related_name='commissions', to='directory.StructuralSubdivision',
                                                  verbose_name='Структурное подразделение')),
            ],
            options={
                'verbose_name': 'Комиссия по проверке знаний',
                'verbose_name_plural': 'Комиссии по проверке знаний',
                'ordering': ['-is_active', 'name'],
            },
        ),
        migrations.CreateModel(
            name='CommissionMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('chairman', '👑 Председатель комиссии'), ('member', '👤 Член комиссии'),
                             ('secretary', '📝 Секретарь комиссии')], default='member', max_length=10,
                    verbose_name='Роль в комиссии')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('commission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members',
                                                 to='directory.Commission', verbose_name='Комиссия')),
                ('employee',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commission_roles',
                                   to='directory.Employee', verbose_name='Сотрудник')),
            ],
            options={
                'verbose_name': 'Участник комиссии',
                'verbose_name_plural': 'Участники комиссии',
                'ordering': ['role', 'employee__full_name_nominative'],
                'unique_together': {('commission', 'employee', 'role')},
            },
        ),
    ]