from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Миграция для обновления модели DocumentTemplate с новым полем выбора типа документа.

    Изменения:
    1. Обновляет список выбора DOCUMENT_TYPES, добавляя 'siz_card' и объединяя
       'internship_order' и 'admission_order' в 'all_orders'
    2. Обновляет существующие записи, изменяя тип документа в соответствии с новой схемой
    """

    dependencies = [
        ('directory', '0006_remove_siznorm_unique_position_siz_empty_condition_and_more'),
    ]

    def update_document_types(apps, schema_editor):
        """
        Функция для обновления типов документов в существующих записях.
        Объединяет 'internship_order' и 'admission_order' в 'all_orders'.
        """
        DocumentTemplate = apps.get_model('directory', 'DocumentTemplate')

        # Обновляем существующие записи
        for template in DocumentTemplate.objects.filter(document_type__in=['internship_order', 'admission_order']):
            template.document_type = 'all_orders'
            template.name = 'Распоряжения о стажировке'
            template.description = 'Шаблон для генерации распоряжений о стажировке и допуске к работе'
            template.save()

    operations = [
        # Сначала обновляем существующие записи
        migrations.RunPython(update_document_types),

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