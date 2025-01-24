from django import forms
from .models import Position, Organization, Employee, Document, OrganizationalUnit


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name_ru',
            'name_by',
            'short_name_ru',
            'short_name_by',
            'requisites_ru',
            'requisites_by',
            'inn'
        ]


class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = ['name', 'code', 'unit_type', 'parent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Исключаем себя и своих потомков из возможных родителей
            self.fields['parent'].queryset = OrganizationalUnit.objects.exclude(
                pk__in=self.instance.get_descendants(include_self=True)
            )

        # Ограничиваем выбор родителя в зависимости от типа
        if self.data.get('unit_type') == 'organization':
            self.fields['parent'].queryset = OrganizationalUnit.objects.none()
        elif self.data.get('unit_type') == 'department':
            self.fields['parent'].queryset = OrganizationalUnit.objects.filter(
                unit_type='organization'
            )
        elif self.data.get('unit_type') == 'division':
            self.fields['parent'].queryset = OrganizationalUnit.objects.filter(
                unit_type='department'
            )

    def clean(self):
        cleaned_data = super().clean()
        unit_type = cleaned_data.get('unit_type')
        parent = cleaned_data.get('parent')

        if unit_type == 'organization' and parent:
            raise forms.ValidationError('Организация не может иметь родительское подразделение')

        if unit_type == 'department' and parent and parent.unit_type != 'organization':
            raise forms.ValidationError('Подразделение может быть создано только в организации')

        if unit_type == 'division' and parent and parent.unit_type != 'department':
            raise forms.ValidationError('Отдел может быть создан только в подразделении')

        return cleaned_data


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор organizational_unit только подразделениями и отделами
        self.fields['organizational_unit'].queryset = OrganizationalUnit.objects.filter(
            unit_type__in=['department', 'division']
        )

    def clean(self):
        cleaned_data = super().clean()
        organizational_unit = cleaned_data.get('organizational_unit')

        if organizational_unit and organizational_unit.unit_type not in ['department', 'division']:
            raise forms.ValidationError('Должность может быть создана только в подразделении или отделе')

        return cleaned_data


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.position:
            unit = self.instance.position.organizational_unit
            self.fields['position'].queryset = Position.objects.filter(
                organizational_unit=unit
            )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'