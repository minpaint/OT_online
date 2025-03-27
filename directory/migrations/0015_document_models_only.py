# Generated manually for document models

import django.core.files.storage
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0013_siz_issued'),  # Убедитесь, что это правильная предыдущая миграция
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Только модели для документов
        migrations.CreateModel(
            name='DocumentTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название шаблона')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('document_type', models.CharField(choices=[('internship_order', '🔖 Распоряжение о стажировке'), ('admission_order', '🔖 Распоряжение о допуске к самостоятельной работе'), ('knowledge_protocol', '📋 Протокол проверки знаний по охране труда'), ('doc_familiarization', '📝 Лист ознакомления с документами')], max_length=50, verbose_name='Тип документа')),
                ('template_file', models.FileField(storage=django.core.files.storage.FileSystemStorage(location='media/document_templates/'), upload_to='document_templates/', verbose_name='Файл шаблона')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Шаблон документа',
                'verbose_name_plural': 'Шаблоны документов',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='GeneratedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_file', models.FileField(upload_to='generated_documents/%Y/%m/%d/', verbose_name='Файл документа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('document_data', models.JSONField(blank=True, default=dict, help_text='Данные, использованные для генерации документа', verbose_name='Данные документа')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Создан пользователем')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='directory.employee', verbose_name='Сотрудник')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='directory.documenttemplate', verbose_name='Шаблон')),
            ],
            options={
                'verbose_name': 'Сгенерированный документ',
                'verbose_name_plural': 'Сгенерированные документы',
                'ordering': ['-created_at'],
            },
        ),
    ]