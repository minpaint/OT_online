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
    class Meta:
        model = SIZNorm
        fields = ('position', 'siz', 'quantity', 'condition', 'order')
        widgets = {
            'position': autocomplete.ModelSelect2(url='directory:position-autocomplete'),
            'siz': autocomplete.ModelSelect2(url='directory:siz-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        position_id = kwargs.pop('position_id', None)
        super().__init__(*args, **kwargs)
        # Если передана должность, устанавливаем ее как начальное значение
        if position_id:
            self.fields['position'].initial = position_id
            self.fields['position'].widget.attrs['readonly'] = True

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
        position = cleaned_data.get('position')
        siz = cleaned_data.get('siz')
        condition = cleaned_data.get('condition', '')

        # Проверка на уникальность нормы
        if position and siz:
            # Ищем существующие нормы для этой комбинации position-siz-condition
            existing_norm = SIZNorm.objects.filter(
                position=position,
                siz=siz,
                condition=condition
            )

            # Исключаем текущий объект при обновлении
            if self.instance and self.instance.pk:
                existing_norm = existing_norm.exclude(pk=self.instance.pk)

            if existing_norm.exists():
                condition_display = condition if condition else "основные нормы"
                raise forms.ValidationError(
                    f"Норма для '{siz}' с условием '{condition_display}' уже существует для должности '{position}'"
                )

        return cleaned_data