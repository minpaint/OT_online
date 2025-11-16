from django import forms
from directory.models.siz import SIZ, SIZNorm
from directory.models.position import Position
from directory.forms.mixins import CrispyFormMixin
from dal import autocomplete


class SIZForm(CrispyFormMixin, forms.ModelForm):
    """
    🛡️ Форма для создания/редактирования СИЗ
    """

    class Meta:
        model = SIZ
        fields = ('name', 'classification', 'unit', 'wear_period')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_tag = True
        self.helper.form_method = 'post'


class SIZNormForm(CrispyFormMixin, forms.ModelForm):
    """
    📋 Форма для создания/редактирования нормы выдачи СИЗ
    """
    # Добавляем поле для выбора уникальной профессии
    unique_position_name = forms.ChoiceField(
        label="Профессия/должность (общее название)",
        required=True,
        help_text="Выберите общее название профессии/должности без привязки к организации"
    )

    class Meta:
        model = SIZNorm
        fields = ('siz', 'quantity', 'condition', 'order')
        # DAL виджет для использования вне админки
        # В админке Django автоматически заменит его на встроенное автозаполнение
        widgets = {
            'siz': autocomplete.ModelSelect2(url='directory:siz-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        position_id = kwargs.pop('position_id', None)
        super().__init__(*args, **kwargs)

        # Получаем список уникальных названий профессий из БД
        unique_positions = Position.objects.values_list('position_name', flat=True).distinct().order_by('position_name')
        self.fields['unique_position_name'].choices = [('', '-- Выберите профессию/должность --')] + [(name, name) for
                                                                                                      name in
                                                                                                      unique_positions]

        # Если форма создается для редактирования существующей нормы
        if self.instance and self.instance.pk and self.instance.position:
            # Предустанавливаем значение профессии
            self.fields['unique_position_name'].initial = self.instance.position.position_name

        # Если передан ID должности, находим её и предустанавливаем значение
        if position_id:
            try:
                position = Position.objects.get(id=position_id)
                self.fields['unique_position_name'].initial = position.position_name
            except Position.DoesNotExist:
                pass

        # Подсказки для поля condition (список существующих условий)
        conditions = SIZNorm.objects.exclude(condition='').values_list('condition', flat=True).distinct()
        if conditions:
            # Добавляем список для автодополнения
            self.fields['condition'].widget.attrs['list'] = 'condition_datalist'
            self.fields['condition'].help_text += '<datalist id="condition_datalist">'
            for condition in set(conditions):
                self.fields['condition'].help_text += f'<option value="{condition}">'
            self.fields['condition'].help_text += '</datalist>'

        self.helper.form_tag = True
        self.helper.form_method = 'post'

    def clean(self):
        """
        ✅ Валидация - проверка на уникальность комбинации position-siz-condition
        """
        cleaned_data = super().clean()
        unique_position_name = cleaned_data.get('unique_position_name')
        siz = cleaned_data.get('siz')
        condition = cleaned_data.get('condition', '')

        # Проверка выбора должности
        if not unique_position_name:
            self.add_error('unique_position_name', 'Необходимо выбрать профессию/должность')
            return cleaned_data

        # Выбираем эталонную должность для выбранного названия (первую в алфавитном порядке по организации)
        reference_position = Position.objects.filter(
            position_name=unique_position_name
        ).order_by('organization__full_name_ru').first()

        if not reference_position:
            self.add_error('unique_position_name', 'Не удалось найти должность с таким названием')
            return cleaned_data

        # Проверка на уникальность нормы
        if siz:
            # Ищем существующие нормы для этой комбинации position-siz-condition
            existing_norm = SIZNorm.objects.filter(
                position=reference_position,
                siz=siz,
                condition=condition
            )

            # Исключаем текущий объект при обновлении
            if self.instance and self.instance.pk:
                existing_norm = existing_norm.exclude(pk=self.instance.pk)

            if existing_norm.exists():
                condition_display = condition if condition else "основные нормы"
                raise forms.ValidationError(
                    f"Норма для '{siz}' с условием '{condition_display}' уже существует для должности '{unique_position_name}'"
                )

        # Сохраняем ссылку на эталонную должность для использования в save()
        self.reference_position = reference_position
        return cleaned_data

    def save(self, commit=True):
        """
        💾 Сохранение нормы СИЗ с привязкой к эталонной должности
        """
        # Устанавливаем эталонную должность для нормы
        self.instance.position = self.reference_position

        return super().save(commit)