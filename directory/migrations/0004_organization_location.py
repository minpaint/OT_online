# Generated by Django 5.0.12 on 2025-03-30 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0003_alter_employee_department_alter_employee_subdivision'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='location',
            field=models.CharField(blank=True, default='г. Минск', help_text='Например: г. Минск, г. Брест и т.д.', max_length=100, verbose_name='Место нахождения'),
        ),
    ]
