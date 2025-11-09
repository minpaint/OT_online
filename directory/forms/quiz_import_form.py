# directory/forms/quiz_import_form.py
"""Формы для импорта вопросов экзамена"""

from django import forms
from directory.models import QuizCategory


class QuizImportForm(forms.Form):
    """Форма для импорта вопросов из Word документа"""

    category = forms.ModelChoiceField(
        queryset=QuizCategory.objects.filter(is_active=True),
        label="Раздел для импорта",
        help_text="Выберите раздел, в который будут импортированы вопросы",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    excel_file = forms.FileField(
        label="Excel файл с вопросами (.xlsx, .xls) - опционально",
        help_text="Выберите файл Excel с вопросами. Правильный ответ должен быть выделен ЖИРНЫМ шрифтом.",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )

    images_zip = forms.FileField(
        label="Архив с изображениями (.zip) - опционально",
        help_text="ZIP архив с изображениями для вопросов (1.jpg для вопроса №1, 2.jpg для вопроса №2 и т.д.)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.zip'})
    )

    replace_existing = forms.BooleanField(
        label="Заменить существующие вопросы в разделе",
        help_text="Если отмечено, все существующие вопросы в разделе будут удалены перед импортом",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        """Валидация формы: хотя бы одно поле должно быть заполнено"""
        cleaned_data = super().clean()
        excel_file = cleaned_data.get('excel_file')
        images_zip = cleaned_data.get('images_zip')

        # Проверяем, что хотя бы один файл загружен
        if not excel_file and not images_zip:
            raise forms.ValidationError(
                'Необходимо загрузить хотя бы один файл: Excel документ с вопросами или ZIP архив с изображениями'
            )

        return cleaned_data

    def clean_excel_file(self):
        """Валидация Excel файла"""
        file = self.cleaned_data.get('excel_file')

        if file:
            # Проверяем расширение
            if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
                raise forms.ValidationError('Файл должен быть в формате .xlsx или .xls')

            # Проверяем размер (макс 10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл слишком большой (макс 10 МБ)')

        return file

    def clean_images_zip(self):
        """Валидация ZIP архива с изображениями"""
        file = self.cleaned_data.get('images_zip')

        if file:
            # Проверяем расширение
            if not file.name.endswith('.zip'):
                raise forms.ValidationError('Файл должен быть в формате .zip')

            # Проверяем размер (макс 50 МБ)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('Архив слишком большой (макс 50 МБ)')

        return file


class QuizImportConfirmForm(forms.Form):
    """Форма подтверждения импорта"""

    confirm = forms.BooleanField(
        label="Подтверждаю импорт",
        required=True,
        widget=forms.HiddenInput()
    )

    session_key = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
