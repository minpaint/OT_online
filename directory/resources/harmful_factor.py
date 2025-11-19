"""
☢️ Resource для импорта/экспорта вредных факторов
"""
from import_export import resources
from deadline_control.models.medical_examination import HarmfulFactor
from django.core.exceptions import ValidationError


class HarmfulFactorResource(resources.ModelResource):
    """
    ☢️ Ресурс для импорта/экспорта вредных производственных факторов.

    Формат Excel файла:
    - short_name - сокращенное наименование (например, "Шум")
    - full_name - полное наименование
    - periodicity - периодичность в месяцах
    """

    class Meta:
        model = HarmfulFactor
        fields = (
            'short_name',
            'full_name',
            'periodicity',
        )
        import_id_fields = []
        skip_unchanged = False

    def before_import_row(self, row, **kwargs):
        """Валидация данных"""

        # Удаляем examination_type если он есть (для обратной совместимости)
        if 'examination_type' in row:
            del row['examination_type']

        # Валидация
        if not row.get('short_name'):
            raise ValidationError('Не указано сокращенное наименование')
        if not row.get('full_name'):
            raise ValidationError('Не указано полное наименование')
        if not row.get('periodicity'):
            raise ValidationError('Не указана периодичность')

    def get_instance(self, instance_loader, row):
        """Ищем существующий вредный фактор по short_name"""
        short_name = row.get('short_name')

        if short_name:
            try:
                return HarmfulFactor.objects.get(short_name=short_name)
            except HarmfulFactor.DoesNotExist:
                pass
        return None
