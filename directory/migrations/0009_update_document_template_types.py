from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0008_update_document_template_choices'),  # Обновлено на последнюю имеющуюся миграцию
    ]

    def update_document_types(apps, schema_editor):
        """
        Функция для обновления типов документов в существующих записях.
        - Объединяет 'internship_order' и 'admission_order' в 'all_orders'
        - Добавляет новый тип 'siz_card'
        """
        DocumentTemplate = apps.get_model('directory', 'DocumentTemplate')

        # Поиск существующих шаблонов
        internship_template = None
        admission_template = None

        try:
            internship_template = DocumentTemplate.objects.get(document_type='internship_order')
        except DocumentTemplate.DoesNotExist:
            pass

        try:
            admission_template = DocumentTemplate.objects.get(document_type='admission_order')
        except DocumentTemplate.DoesNotExist:
            pass

        # Если найден хотя бы один из шаблонов, создаем комбинированный шаблон
        if internship_template or admission_template:
            # Берем первый найденный шаблон как основу
            base_template = internship_template or admission_template

            # Обновляем тип и название
            base_template.document_type = 'all_orders'
            base_template.name = 'Распоряжения о стажировке'
            base_template.description = 'Шаблон для генерации распоряжений о стажировке и допуске к работе'
            base_template.save()

            # Удаляем второй шаблон, если он существует и отличается от первого
            if internship_template and admission_template and internship_template.id != admission_template.id:
                admission_template.delete()

    def reverse_migration(apps, schema_editor):
        """
        Функция для отката изменений (если потребуется).
        """
        DocumentTemplate = apps.get_model('directory', 'DocumentTemplate')

        # Находим шаблон 'all_orders'
        try:
            combined_template = DocumentTemplate.objects.get(document_type='all_orders')
            # Меняем тип обратно на 'internship_order'
            combined_template.document_type = 'internship_order'
            combined_template.name = 'Распоряжение о стажировке'
            combined_template.description = 'Шаблон для генерации распоряжения о стажировке'
            combined_template.save()
        except DocumentTemplate.DoesNotExist:
            pass

    operations = [
        # Сначала обновляем существующие записи
        migrations.RunPython(update_document_types, reverse_migration),

        # Затем изменяем поле выбора
        migrations.AlterField(
            model_name='documenttemplate',
            name='document_type',
            field=models.CharField(
                choices=[
                    ('all_orders', '📝 Распоряжения о стажировке'),
                    ('knowledge_protocol', '📋 Протокол проверки знаний по охране труда'),
                    ('doc_familiarization', '📝 Лист ознакомления с документами'),
                    ('siz_card', '🛡️ Карточка учета СИЗ')
                ],
                max_length=50,
                verbose_name='Тип документа'
            ),
        ),
    ]