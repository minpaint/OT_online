# Generated by Django 5.0.12 on 2025-04-20 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0015_rename_maintenance_period_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='maintenance_period_months',
            field=models.PositiveIntegerField(default=12, verbose_name='Периодичность ТО (месяцев)'),
        ),
    ]
