# directory/resources/siz_norm.py
from import_export import resources, fields, widgets
from directory.models.siz import SIZNorm, SIZ
from directory.models.position import Position


class SIZWidget(widgets.ForeignKeyWidget):
    """🛡️ Виджет для поиска или создания СИЗ по названию

    Если СИЗ не найдено - создаёт новое с параметрами из строки импорта
    """

    def clean(self, value, row=None, **kwargs):
        """Ищет СИЗ по названию или создаёт новое"""
        if not value:
            return None

        try:
            # Ищем СИЗ по точному совпадению названия
            return self.get_queryset(value, row, **kwargs).get(
                **{f'{self.field}__iexact': value}
            )
        except self.model.DoesNotExist:
            # СИЗ не найдено - создаём новое с параметрами из строки
            # Параметры берём из row (строки импорта)
            classification = row.get('Классификация (маркировка)', '') if row else ''
            unit = row.get('Единица измерения', 'шт.') if row else 'шт.'
            wear_period_str = row.get('Срок носки', '12') if row else '12'

            # Обрабатываем срок носки (может быть числом или текстом)
            wear_period = 12
            wear_type = ''

            if isinstance(wear_period_str, str):
                wear_period_lower = wear_period_str.strip().lower()
                special_types = {
                    'до износа': ('До износа', 0),
                    'доизноса': ('До износа', 0),
                    'до_износа': ('До износа', 0),
                    'дежурный': ('Дежурный', 0),
                    'дежурная': ('Дежурная', 0),
                    'дежурные': ('Дежурные', 0),
                    'дежурное': ('Дежурное', 0)
                }

                if wear_period_lower in special_types:
                    wear_type, wear_period = special_types[wear_period_lower]
                else:
                    try:
                        wear_period = int(wear_period_str)
                        wear_type = ''
                    except (ValueError, TypeError):
                        wear_period = 12
                        wear_type = ''
            else:
                try:
                    wear_period = int(wear_period_str)
                    wear_type = ''
                except (ValueError, TypeError):
                    wear_period = 12
                    wear_type = ''

            # Создаём новое СИЗ
            new_siz = SIZ.objects.create(
                name=value,
                classification=classification or '',
                unit=unit,
                wear_period=wear_period,
                wear_type=wear_type
            )

            return new_siz

        except self.model.MultipleObjectsReturned:
            # Найдено несколько - берём первое
            return self.get_queryset(value, row, **kwargs).filter(
                **{f'{self.field}__iexact': value}
            ).first()


class PositionWidget(widgets.ForeignKeyWidget):
    """👔 Виджет для поиска должности по названию"""

    def clean(self, value, row=None, **kwargs):
        """Ищет должность по названию профессии"""
        if not value:
            return None

        # Ищем эталонную должность с таким названием (первую по алфавиту организаций)
        position = Position.objects.filter(
            position_name__iexact=value
        ).order_by('organization__full_name_ru').first()

        if not position:
            raise ValueError(f"Должность '{value}' не найдена")

        return position


class SIZNormResource(resources.ModelResource):
    """🔄 Ресурс для импорта/экспорта норм выдачи СИЗ

    Формат файла Excel (расширенный):
    - Профессия/должность (текст) - название профессии
    - СИЗ (текст) - название СИЗ
    - Классификация (маркировка) (текст) - маркировка СИЗ (если СИЗ нет в справочнике)
    - Единица измерения (текст) - единица измерения (по умолчанию "шт.")
    - Срок носки (число/текст) - срок в месяцах или "До износа"/"Дежурный"
    - Количество (число) - количество единиц для выдачи
    - Условие выдачи (текст) - условие выдачи, пустое = основная норма

    ВАЖНО: Порядок норм определяется порядком строк в файле!

    Логика импорта:
    1. Ищет СИЗ в справочнике по названию
    2. Если не найдено - создаёт новое с указанными параметрами
    3. Если найдено - использует существующее (параметры СИЗ игнорируются)
    4. Порядок отображения = номер строки в файле
    """

    position = fields.Field(
        column_name='Профессия/должность',
        attribute='position',
        widget=PositionWidget(Position, field='position_name')
    )

    siz = fields.Field(
        column_name='СИЗ',
        attribute='siz',
        widget=SIZWidget(SIZ, field='name')
    )

    # Дополнительные поля для создания СИЗ (не сохраняются в SIZNorm)
    classification = fields.Field(
        column_name='Классификация (маркировка)',
        attribute='siz__classification',
        readonly=True
    )

    unit = fields.Field(
        column_name='Единица измерения',
        attribute='siz__unit',
        readonly=True
    )

    wear_period_display = fields.Field(
        column_name='Срок носки',
        attribute='siz__wear_period',
        readonly=True
    )

    quantity = fields.Field(
        column_name='Количество',
        attribute='quantity'
    )

    condition = fields.Field(
        column_name='Условие выдачи',
        attribute='condition'
    )

    class Meta:
        model = SIZNorm
        fields = ('position', 'siz', 'classification', 'unit', 'wear_period_display',
                  'quantity', 'condition')
        export_order = ('position', 'siz', 'classification', 'unit', 'wear_period_display',
                        'quantity', 'condition')
        import_id_fields = ['position', 'siz', 'condition']  # Уникальная комбинация
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, row_number=None, **kwargs):
        """Предобработка строки перед импортом"""
        # Устанавливаем значения по умолчанию
        if 'Условие выдачи' not in row or not row['Условие выдачи']:
            row['Условие выдачи'] = ''

        if 'Количество' not in row or not row['Количество']:
            row['Количество'] = 1

        # Устанавливаем порядок равным номеру строки
        # row_number начинается с 2 (1 - заголовки), поэтому вычитаем 1
        if row_number is not None:
            row['_order'] = row_number - 1
        else:
            row['_order'] = 0

    def after_import_instance(self, instance, new, row=None, **kwargs):
        """Установка порядка после создания экземпляра"""
        if row and '_order' in row:
            instance.order = row['_order']

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Пропускаем строки с пустыми обязательными полями"""
        # Пропускаем, если нет профессии или СИЗ
        if not row.get('Профессия/должность') or not row.get('СИЗ'):
            return True

        return super().skip_row(instance, original, row, import_validation_errors)
