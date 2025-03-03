# Generated by Django 5.0.12 on 2025-02-27 18:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0010_ppecategory_ppeitem_ppeissued_positionppe'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeePPEOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('override_type', models.CharField(choices=[('add', 'Добавить СИЗ'), ('exclude', 'Исключить СИЗ'), ('modify', 'Изменить количество/период')], default='add', max_length=10, verbose_name='Тип исключения')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, help_text="Используется для типа 'Добавить' или 'Изменить'", max_digits=5, verbose_name='Количество')),
                ('period_months', models.PositiveIntegerField(default=12, help_text="Используется для типа 'Добавить' или 'Изменить'", verbose_name='Период замены (мес)')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ppe_overrides', to='directory.employee', verbose_name='Сотрудник')),
                ('ppe_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='directory.ppeitem', verbose_name='СИЗ')),
            ],
            options={
                'verbose_name': 'Индивидуальное исключение СИЗ',
                'verbose_name_plural': 'Индивидуальные исключения СИЗ',
                'unique_together': {('employee', 'ppe_item')},
            },
        ),
    ]
