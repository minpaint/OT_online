from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from directory.models import Profile, Organization
from django_select2 import forms as s2forms

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации пользователя с расширенными возможностями.

    Особенности:
    - Валидация email и пароля.
    - Выбор организаций через Select2.
    - Автоматическое создание профиля.
    - Интернационализация сообщений об ошибках.
    """

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.all(),
        widget=s2forms.Select2MultipleWidget(attrs={
            'class': 'form-control',
            'data-placeholder': _("Выберите организации...")
        }),
        required=False,
        label=_("Организации, к которым предоставить доступ")
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'organizations'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })
        self.fields['password2'].label = _("Confirm Password")

    def clean_email(self):
        """Проверка уникальности email."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Пользователь с таким email уже существует."))
        return email

    def clean_password2(self):
        """Проверка совпадения паролей и их сложности."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Пароли не совпадают."))

        from django.contrib.auth.password_validation import validate_password
        validate_password(password2, self.instance)

        return password2

    def save(self, commit=True):
        """
        Сохранение пользователя с созданием профиля и привязкой к организациям.
        Используем транзакцию для атомарности операций.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            from django.db import transaction
            with transaction.atomic():
                user.save()
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.organizations.set(self.cleaned_data['organizations'])
        return user
