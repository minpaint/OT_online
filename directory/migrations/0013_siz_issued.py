# 📁 directory/migrations/0013_siz_issued.py
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0012_siz_remove_positionppe_position_and_more'),  # Убедитесь, что это последняя миграция
    ]

    operations = [
        migrations.CreateModel(
            name='SIZIssued',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_date', models.DateField(default=timezone.now, verbose_name='Дата выдачи')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('wear_percentage', models.PositiveIntegerField(default=0, help_text='Укажите процент износа от 0 до 100', verbose_name='Процент износа')),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Стоимость')),
                ('replacement_date', models.DateField(blank=True, null=True, verbose_name='Дата замены/списания')),
                ('is_returned', models.BooleanField(default=False, verbose_name='Возвращено')),
                ('return_date', models.DateField(blank=True, null=True, verbose_name='Дата возврата')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('condition', models.CharField(blank=True, help_text='Условие, при котором выдано СИЗ', max_length=255, verbose_name='Условие выдачи')),
                ('received_signature', models.BooleanField(default=False, verbose_name='Подпись о получении')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issued_siz', to='directory.employee', verbose_name='Сотрудник')),
                ('siz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='directory.siz', verbose_name='СИЗ')),
            ],
            options={
                'verbose_name': 'Выданное СИЗ',
                'verbose_name_plural': 'Выданные СИЗ',
                'ordering': ['-issue_date', 'employee__full_name_nominative'],
            },
        ),
    ]