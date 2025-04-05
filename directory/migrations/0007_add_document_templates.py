from django.db import migrations, models
import django.db.models.deletion
from django.core.files.storage import FileSystemStorage

document_storage = FileSystemStorage(location='media/document_templates/')


class Migration(migrations.Migration):
    """
    Миграция для создания моделей DocumentTemplate и GeneratedDocument.

    Создает необходимые модели для работы с шаблонами документов и
    хранения сгенерированных документов.
    """

    dependencies = [
        ('directory', '0006_remove_siznorm_unique_position_siz_empty_condition_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Стандартная зависимость для модели User
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название шаблона')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('document_type', models.CharField(
                    choices=[
                        ('internship_order', 'Распоряжение о стажировке'),
                        ('admission_order', 'Распоряжение о допуске к работе'),
                        ('knowledge_protocol', 'Протокол проверки знаний по охране труда'),
                        ('doc_familiarization', 'Лист ознакомления с документами')
                    ],
                    max_length=50,
                    verbose_name='Тип документа'
                )),
                ('template_file', models.FileField(storage=document_storage, upload_to='document_templates/',
                                                   verbose_name='Файл шаблона')),
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
                ('document_file',
                 models.FileField(upload_to='generated_documents/%Y/%m/%d/', verbose_name='Файл документа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('document_data',
                 models.JSONField(blank=True, default=dict, help_text='Данные, использованные для генерации документа',
                                  verbose_name='Данные документа')),
                ('created_by',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user',
                                   verbose_name='Создан пользователем')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents',
                                               to='directory.employee', verbose_name='Сотрудник')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                               to='directory.documenttemplate', verbose_name='Шаблон')),
            ],
            options={
                'verbose_name': 'Сгенерированный документ',
                'verbose_name_plural': 'Сгенерированные документы',
                'ordering': ['-created_at'],
            },
        ),
    ]