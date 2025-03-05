from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, HTML, Div
from directory.models.siz_issued import SIZIssued
from directory.models.siz import SIZNorm, SIZ
from directory.models.employee import Employee


class SIZIssueMassForm(forms.Form):
    """
    📝 Форма для массовой выдачи СИЗ сотруднику

    Позволяет выбрать сотрудника и сразу несколько СИЗ для выдачи с заполнением
    информации о количестве, дате и т.д.
    """
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label="Сотрудник",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    issue_date = forms.DateField(
        label="Дата выдачи",
        required=True,
        initial=timezone.now,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        )
    )

    def __init__(self, *args, **kwargs):
        """
        🏗️ Инициализация формы с динамическими полями для СИЗ
        """
        self.user = kwargs.pop('user', None)
        self.employee_id = kwargs.pop('employee_id', None)
        super().__init__(*args, **kwargs)

        # Инициализация helper для crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'

        # Ограничиваем выбор сотрудников по организациям пользователя
        if self.user and hasattr(self.user, 'profile'):
            allowed_orgs = self.user.profile.organizations.all()
            self.fields['employee'].queryset = Employee.objects.filter(
                organization__in=allowed_orgs
            ).order_by('full_name_nominative')

        # Устанавливаем выбранного сотрудника, если он передан
        if self.employee_id:
            try:
                self.fields['employee'].initial = Employee.objects.get(pk=self.employee_id)
            except Employee.DoesNotExist:
                pass

        # Динамически добавляем поля на основе норм СИЗ для должности сотрудника
        self.setup_siz_fields()

        # Настраиваем layout для формы
        self.setup_layout()

    def setup_siz_fields(self):
        """
        🔧 Настройка динамических полей для выбора СИЗ
        """
        if 'employee' in self.data and self.data['employee']:
            # Если форма уже отправлена, используем выбранного сотрудника
            try:
                employee = Employee.objects.get(pk=self.data['employee'])
                self.add_siz_fields_for_employee(employee)
            except (Employee.DoesNotExist, ValueError):
                pass
        elif self.fields['employee'].initial:
            # Если есть начальное значение, используем его
            self.add_siz_fields_for_employee(self.fields['employee'].initial)

    def add_siz_fields_for_employee(self, employee):
        """
        ➕ Добавление полей для СИЗ конкретного сотрудника

        Получает нормы СИЗ для должности сотрудника и создает для каждой нормы поля
        выбора, количества и примечаний
        """
        if not employee.position:
            return

        # Получаем все нормы СИЗ для должности сотрудника
        norms = SIZNorm.objects.filter(
            position=employee.position
        ).select_related('siz').order_by('condition', 'order', 'siz__name')

        # Группируем нормы по условиям
        conditions_groups = {}
        for norm in norms:
            condition = norm.condition or "Основные СИЗ"
            if condition not in conditions_groups:
                conditions_groups[condition] = []
            conditions_groups[condition].append(norm)

        # Для каждой нормы создаем набор полей
        for condition, condition_norms in conditions_groups.items():
            for norm in condition_norms:
                field_prefix = f"siz_{norm.id}"

                # Поле для выбора СИЗ (чекбокс)
                self.fields[f"{field_prefix}_select"] = forms.BooleanField(
                    label=f"{norm.siz.name} ({norm.siz.classification})",
                    required=False,
                    initial=False,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input siz-select',
                        'data-norm-id': norm.id,
                        'data-condition': condition
                    })
                )

                # Поле для количества
                self.fields[f"{field_prefix}_quantity"] = forms.IntegerField(
                    label="Количество",
                    required=False,
                    initial=norm.quantity,
                    min_value=1,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control siz-quantity',
                        'data-norm-id': norm.id
                    })
                )

                # Поле для примечаний
                self.fields[f"{field_prefix}_notes"] = forms.CharField(
                    label="Примечания",
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control siz-notes',
                        'data-norm-id': norm.id
                    })
                )

                # Поле для стоимости
                self.fields[f"{field_prefix}_cost"] = forms.DecimalField(
                    label="Стоимость",
                    required=False,
                    decimal_places=2,
                    max_digits=10,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control siz-cost',
                        'data-norm-id': norm.id,
                        'step': '0.01'
                    })
                )

                # Скрытое поле с ID нормы и СИЗ
                self.fields[f"{field_prefix}_norm_id"] = forms.IntegerField(
                    widget=forms.HiddenInput(),
                    initial=norm.id
                )
                self.fields[f"{field_prefix}_siz_id"] = forms.IntegerField(
                    widget=forms.HiddenInput(),
                    initial=norm.siz.id
                )
                self.fields[f"{field_prefix}_condition"] = forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=norm.condition
                )

    def setup_layout(self):
        """
        🎨 Настройка layout для формы
        """
        layout_objects = [
            Fieldset(
                'Информация о выдаче',
                Row(
                    Column('employee', css_class='col-md-6'),
                    Column('issue_date', css_class='col-md-6'),
                    css_class='form-row'
                ),
                css_class='border p-3 mb-3 rounded'
            ),
            HTML("<div id='siz-groups-container'></div>"),
            Div(
                Submit('submit', '💾 Выдать СИЗ', css_class='btn-primary'),
                HTML('<a href="{% url "directory:siz:siz_list" %}" class="btn btn-secondary ml-2">Отмена</a>'),
                css_class='text-center mt-3'
            )
        ]

        self.helper.layout = Layout(*layout_objects)

    def save(self, commit=True):
        """
        💾 Сохранение выбранных СИЗ

        Создает объекты SIZIssued для каждого выбранного СИЗ
        """
        if not commit:
            return []

        employee = self.cleaned_data['employee']
        issue_date = self.cleaned_data['issue_date']

        # Создаем список для хранения созданных объектов
        created_objects = []

        # Проходим по всем полям формы, ищем выбранные СИЗ
        for field_name, value in self.cleaned_data.items():
            if field_name.endswith('_select') and value:
                # Получаем ID нормы из имени поля
                norm_id = field_name.split('_')[1]

                # Получаем соответствующие поля для этой нормы
                siz_id = self.cleaned_data.get(f"siz_{norm_id}_siz_id")
                quantity = self.cleaned_data.get(f"siz_{norm_id}_quantity", 1)
                notes = self.cleaned_data.get(f"siz_{norm_id}_notes", "")
                cost = self.cleaned_data.get(f"siz_{norm_id}_cost")
                condition = self.cleaned_data.get(f"siz_{norm_id}_condition", "")

                # Проверяем существование СИЗ
                try:
                    siz = SIZ.objects.get(pk=siz_id)

                    # Создаем запись о выдаче СИЗ
                    issued = SIZIssued.objects.create(
                        employee=employee,
                        siz=siz,
                        issue_date=issue_date,
                        quantity=quantity,
                        notes=notes,
                        cost=cost,
                        condition=condition,
                        received_signature=True # По умолчанию считаем, что подпись получена
                    )

                    created_objects.append(issued)

                except SIZ.DoesNotExist:
                    continue

        return created_objects


class SIZIssueReturnForm(forms.ModelForm):
    """
    📝 Форма для возврата выданного СИЗ
    """
    class Meta:
        model = SIZIssued
        fields = ['return_date', 'wear_percentage', 'notes']
        widgets = {
            'return_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'wear_percentage': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['return_date'].initial = timezone.now
        self.fields['return_date'].required = True

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Подтвердить возврат', css_class='btn-primary'))

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_returned = True

        if commit:
            instance.save()

        return instance