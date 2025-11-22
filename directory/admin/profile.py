# directory/admin/profile.py
from django.contrib import admin
from django.forms import ModelForm
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from directory.models import Profile, Organization, StructuralSubdivision, Department, MenuItem


class HierarchicalAccessWidget(forms.Widget):
    """
    Кастомный виджет для иерархического выбора доступа с деревом:
    Организация → Подразделения → Отделы
    """
    template_name = 'admin/directory/profile/hierarchical_access_widget.html'

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Получаем все организации с их подразделениями и отделами
        organizations = Organization.objects.prefetch_related(
            'subdivisions__departments'
        ).order_by('short_name_ru')

        # Если value - это существующий профиль, получаем выбранные элементы
        selected_orgs = set()
        selected_subdivs = set()
        selected_depts = set()

        if value:
            if isinstance(value, dict):
                selected_orgs = set(value.get('organizations', []))
                selected_subdivs = set(value.get('subdivisions', []))
                selected_depts = set(value.get('departments', []))

        # Формируем структуру данных для шаблона
        context['organizations_tree'] = []
        for org in organizations:
            org_data = {
                'id': org.id,
                'name': org.short_name_ru,
                'checked': org.id in selected_orgs,
                'subdivisions': []
            }

            for subdiv in org.subdivisions.all():
                subdiv_data = {
                    'id': subdiv.id,
                    'name': subdiv.name,
                    'checked': subdiv.id in selected_subdivs,
                    'departments': []
                }

                for dept in subdiv.departments.all():
                    dept_data = {
                        'id': dept.id,
                        'name': dept.name,
                        'checked': dept.id in selected_depts,
                    }
                    subdiv_data['departments'].append(dept_data)

                org_data['subdivisions'].append(subdiv_data)

            context['organizations_tree'].append(org_data)

        return context

    def value_from_datadict(self, data, files, name):
        """Извлекаем выбранные значения из POST данных"""
        organizations = data.getlist(f'{name}_organizations')
        subdivisions = data.getlist(f'{name}_subdivisions')
        departments = data.getlist(f'{name}_departments')

        return {
            'organizations': [int(x) for x in organizations if x],
            'subdivisions': [int(x) for x in subdivisions if x],
            'departments': [int(x) for x in departments if x],
        }


class ProfileAdminForm(ModelForm):
    """Кастомная форма для Profile с иерархическим выбором доступа"""

    hierarchical_access = forms.Field(
        widget=HierarchicalAccessWidget(),
        required=False,
        label="Иерархический доступ",
        help_text="Выберите организации, подразделения или отделы, к которым пользователь будет иметь доступ"
    )

    visible_menu_items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.filter(is_active=True).order_by('location', 'parent__order', 'order', 'name'),
        required=False,
        widget=FilteredSelectMultiple('Пункты меню', is_stacked=False),
        label="Доступные пункты меню",
        help_text="🍔 Выберите пункты меню, доступные пользователю. Если не выбраны - доступны все активные пункты."
    )

    class Meta:
        model = Profile
        fields = ['user', 'is_active', 'visible_menu_items']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если редактируем существующий профиль, заполняем hierarchical_access
        if self.instance and self.instance.pk:
            self.initial['hierarchical_access'] = {
                'organizations': list(self.instance.organizations.values_list('id', flat=True)),
                'subdivisions': list(self.instance.subdivisions.values_list('id', flat=True)),
                'departments': list(self.instance.departments.values_list('id', flat=True)),
            }
            # Заполняем visible_menu_items
            self.initial['visible_menu_items'] = self.instance.visible_menu_items.all()

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

        # Сохраняем M2M связи из hierarchical_access
        if 'hierarchical_access' in self.cleaned_data:
            access_data = self.cleaned_data['hierarchical_access']

            if isinstance(access_data, dict):
                # Устанавливаем организации
                org_ids = access_data.get('organizations', [])
                instance.organizations.set(Organization.objects.filter(id__in=org_ids))

                # Устанавливаем подразделения
                subdiv_ids = access_data.get('subdivisions', [])
                instance.subdivisions.set(StructuralSubdivision.objects.filter(id__in=subdiv_ids))

                # Устанавливаем отделы
                dept_ids = access_data.get('departments', [])
                instance.departments.set(Department.objects.filter(id__in=dept_ids))

        # Сохраняем видимые пункты меню
        if 'visible_menu_items' in self.cleaned_data:
            instance.visible_menu_items.set(self.cleaned_data['visible_menu_items'])

        return instance


# ProfileAdmin убран - профиль редактируется только через inline в User админке
