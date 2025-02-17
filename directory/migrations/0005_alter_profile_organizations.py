# Generated by Django 5.0.12 on 2025-02-17 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0004_create_profiles_for_existing_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='organizations',
            field=models.ManyToManyField(help_text='🏢 Организации, к которым у пользователя есть доступ (выберите одну или несколько)', related_name='user_profiles', to='directory.organization', verbose_name='Организации'),
        ),
    ]
