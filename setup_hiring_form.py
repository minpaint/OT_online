import os
import shutil
from pathlib import Path
import sys
import locale

# Установка кодировки по умолчанию
sys.stdout.reconfigure(encoding='utf-8')

# Содержимое файлов
FILES = {
    # Models
    'models/profile.py': '''from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    👤 Профиль пользователя с доступом к организациям
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    organizations = models.ManyToManyField(
        'directory.Organization',
        verbose_name="Организации",
        related_name="user_profiles",
        help_text="Организации, к которым у пользователя есть доступ"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль пользователя {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля при создании пользователя"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля при сохранении пользователя"""
    instance.profile.save()
''',

    # Forms
    'forms/employee_hiring.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from dal import autocomplete
from directory.models import Employee

class EmployeeHiringForm(forms.ModelForm):
    """
    📝 Форма приема на работу
    """
    preview = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Employee
        fields = [
            'full_name_nominative',
            'full_name_dative',
            'date_of_birth',
            'place_of_residence',
            'organization',
            'subdivision',
            'department',
            'position',
            'height',
            'clothing_size',
            'shoe_size',
            'is_contractor'
        ]
        widgets = {
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={'data-placeholder': '🏢 Выберите организацию...'}
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={'data-placeholder': '🏭 Выберите подразделение...'}
            ),
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'data-minimum-input-length': 0
                }
            ),
            'position': autocomplete.ModelSelect2(
                url='directory:position-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={'data-placeholder': '👔 Выберите должность...'}
            ),
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('full_name_nominative', css_class='form-group col-md-6'),
                Column('full_name_dative', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('date_of_birth', css_class='form-group col-md-6'),
                Column('place_of_residence', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('organization', css_class='form-group col-md-6'),
                Column('subdivision', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('department', css_class='form-group col-md-6'),
                Column('position', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('height', css_class='form-group col-md-4'),
                Column('clothing_size', css_class='form-group col-md-4'),
                Column('shoe_size', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            'is_contractor',
            HTML("<hr>"),
            Row(
                Column(
                    Submit('preview', '👁 Предпросмотр', css_class='btn-info'),
                    css_class='form-group col-6'
                ),
                Column(
                    Submit('submit', '💾 Принять на работу', css_class='btn-success'),
                    css_class='form-group col-6'
                ),
                css_class='form-row'
            )
        )

        if user:
            # Фильтруем организации по доступу пользователя
            self.fields['organization'].queryset = user.profile.organizations.all()
''',

    # Views
    'views/home.py': '''from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
from directory.forms import EmployeeHiringForm
from directory.models import Employee
import logging

logger = logging.getLogger(__name__)

class HomePageView(LoginRequiredMixin, CreateView):
    """
    🏠 Главная страница с формой приема на работу
    """
    template_name = 'directory/home.html'
    form_class = EmployeeHiringForm
    success_url = reverse_lazy('directory:home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data.get('preview'):
            # Режим предпросмотра
            return render(self.request, 'directory/preview.html', {
                'form': form,
                'data': form.cleaned_data
            })

        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f"✅ Сотрудник {form.instance.full_name_nominative} успешно принят на работу"
            )
            # Логируем успешное действие
            logger.info(
                f"User {self.request.user} hired employee {form.instance}",
                extra={
                    'user_id': self.request.user.id,
                    'employee_id': form.instance.id
                }
            )
            return response
        except Exception as e:
            # Логируем ошибку
            logger.error(
                f"Error hiring employee: {str(e)}",
                extra={
                    'user_id': self.request.user.id,
                    'form_data': form.cleaned_data
                }
            )
            messages.error(
                self.request,
                f"❌ Ошибка при приеме на работу: {str(e)}"
            )
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_employees'] = Employee.objects.filter(
            organization__in=self.request.user.profile.organizations.all()
        ).order_by('-id')[:5]
        return context
''',

    # Templates
    'templates/directory/home.html': '''{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load static %}

{% block extra_css %}
<link href="{% static 'css/select2.min.css' %}" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h3>📝 Прием на работу</h3>
                </div>
                <div class="card-body">
                    <form method="post" id="hiring-form">
                        {% csrf_token %}
                        {{ form|crispy }}
                    </form>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h4>📊 Последние принятые</h4>
                </div>
                <div class="card-body">
                    {% if recent_employees %}
                        <ul class="list-group">
                        {% for employee in recent_employees %}
                            <li class="list-group-item">
                                <strong>{{ employee.full_name_nominative }}</strong><br>
                                <small>{{ employee.position }} ({{ employee.organization.short_name_ru }})</small>
                            </li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        <p class="text-muted">Нет недавно принятых сотрудников</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Модальное окно для предпросмотра -->
<div class="modal fade" id="previewModal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">👁 Предпросмотр данных</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body" id="preview-content">
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/select2.min.js' %}"></script>
<script>
$(document).ready(function() {
    // Инициализация Select2
    $('.select2').select2();

    // Обработка предпросмотра
    $('#hiring-form button[name="preview"]').click(function(e) {
        e.preventDefault();
        var form = $('#hiring-form');
        form.find('input[name="preview"]').val('true');

        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            success: function(response) {
                $('#preview-content').html(response);
                $('#previewModal').modal('show');
            }
        });
    });
});
</script>
{% endblock %}''',

    'templates/directory/preview.html': '''<div class="container">
    <div class="row">
        <div class="col-12">
            <h4>📋 Проверьте данные перед сохранением</h4>
            <table class="table table-bordered">
                <tr>
                    <th>ФИО (именительный)</th>
                    <td>{{ data.full_name_nominative }}</td>
                </tr>
                <tr>
                    <th>ФИО (дательный)</th>
                    <td>{{ data.full_name_dative }}</td>
                </tr>
                <tr>
                    <th>Дата рождения</th>
                    <td>{{ data.date_of_birth }}</td>
                </tr>
                <tr>
                    <th>Место проживания</th>
                    <td>{{ data.place_of_residence }}</td>
                </tr>
                <tr>
                    <th>Организация</th>
                    <td>{{ data.organization }}</td>
                </tr>
                <tr>
                    <th>Подразделение</th>
                    <td>{{ data.subdivision|default:"—" }}</td>
                </tr>
                <tr>
                    <th>Отдел</th>
                    <td>{{ data.department|default:"—" }}</td>
                </tr>
                <tr>
                    <th>Должность</th>
                    <td>{{ data.position }}</td>
                </tr>
                <tr>
                    <th>Рост</th>
                    <td>{{ data.height|default:"—" }}</td>
                </tr>
                <tr>
                    <th>Размер одежды</th>
                    <td>{{ data.clothing_size|default:"—" }}</td>
                </tr>
                <tr>
                    <th>Размер обуви</th>
                    <td>{{ data.shoe_size|default:"—" }}</td>
                </tr>
                <tr>
                    <th>Договор подряда</th>
                    <td>{% if data.is_contractor %}Да{% else %}Нет{% endif %}</td>
                </tr>
            </table>
        </div>
    </div>
    <div class="row">
        <div class="col-12 text-right">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">✏️ Изменить</button>
            <button type="submit" form="hiring-form" class="btn btn-success">💾 Подтвердить</button>
        </div>
    </div>
</div>''',

    # URLs update
    'urls.py': '''from django.urls import path
from . import views

app_name = 'directory'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    # ... существующие URLs ...
]''',

    # Tests
    'tests/test_profile.py': '''from django.test import TestCase
from django.contrib.auth.models import User
from directory.models import Profile, Organization

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Org',
            short_name='TO'
        )

    def test_profile_creation(self):
        """Тест автоматического создания профиля"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_organization_assignment(self):
        """Тест назначения организации пользователю"""
        self.user.profile.organizations.add(self.org)
        self.assertIn(self.org, self.user.profile.organizations.all())
''',

    'tests/test_employee_hiring.py': '''from django.test import TestCase
from django.contrib.auth.models import User
from directory.models import Organization, Employee
from directory.forms import EmployeeHiringForm

class EmployeeHiringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Org',
            short_name='TO'
        )
        self.user.profile.organizations.add(self.org)

    def test_form_organization_filtering(self):
        """Тест фильтрации организаций в форме"""
        form = EmployeeHiringForm(user=self.user)
        self.assertEqual(
            list(form.fields['organization'].queryset),
            list(self.user.profile.organizations.all())
        )

    def test_employee_creation(self):
        """Тест создания сотрудника через форму"""
        form_data = {
            'full_name_nominative': 'Test Employee',
            'full_name_dative': 'Test Employee',
            'organization': self.org.id,
            'date_of_birth': '2000-01-01'
        }
        form = EmployeeHiringForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
''',
}


def create_directory_structure():
    """Создание структуры директорий и файлов"""
    base_dir = Path('directory')

    # Создаем директории
    directories = [
        'models',
        'forms',
        'views',
        'templates/directory',
        'tests',
    ]

    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # Создаем __init__.py в каждой Python-директории
        if 'templates' not in directory:
            init_file = dir_path / '__init__.py'
            init_file.touch()

    # Создаем файлы с содержимым
    for file_path, content in FILES.items():
        full_path = base_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Добавляем encoding='utf-8'
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)


def update_requirements():
    """Обновление requirements.txt"""
    requirements = '''
django-crispy-forms>=2.0
django-autocomplete-light>=3.9.4
django-select2>=8.1.2
'''
    # Добавляем encoding='utf-8'
    with open('requirements.txt', 'a', encoding='utf-8') as f:
        f.write(requirements)


def main():
    """Основная функция"""
    try:
        create_directory_structure()
        update_requirements()
        print("✅ Структура проекта успешно создана!")
        print("\n📋 Следующие шаги:")
        print("1. Выполните: pip install -r requirements.txt")
        print("2. Добавьте 'dal', 'dal_select2', 'crispy_forms' в INSTALLED_APPS")
        print("3. Выполните: python manage.py makemigrations")
        print("4. Выполните: python manage.py migrate")
        print("5. Проверьте настройки URLs")
        print("6. Соберите статические файлы: python manage.py collectstatic")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == '__main__':
    main()