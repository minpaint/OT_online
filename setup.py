#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для создания пустых файлов проекта многошаговой формы
"""
import os
import sys


def create_directory(path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Создана директория: {path}")
    else:
        print(f"ℹ️ Директория уже существует: {path}")


def create_file(path, content=""):
    """Создает пустой файл с базовым содержимым"""
    # Проверяем, не существует ли файл уже
    if os.path.exists(path):
        print(f"⚠️ Файл уже существует, пропускаем: {path}")
        return False

    # Создаем директорию для файла, если она не существует
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # Создаем файл
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Создан файл: {path}")
    return True


def main():
    # Базовая директория проекта (измените на свою)
    base_dir = os.path.abspath(os.getcwd())

    # Определяем пути к директориям
    dirs = {
        'forms': os.path.join(base_dir, 'directory', 'forms'),
        'views': os.path.join(base_dir, 'directory', 'views'),
        'templates': os.path.join(base_dir, 'templates', 'directory', 'hiring'),
        'api': os.path.join(base_dir, 'directory', 'api'),
    }

    # Создаем необходимые директории
    for dir_path in dirs.values():
        create_directory(dir_path)

    # Файлы для создания
    files = [
        # Формы
        {
            'path': os.path.join(dirs['forms'], 'hiring_wizard.py'),
            'content': '''# -*- coding: utf-8 -*-
"""
📝 Формы для многошаговой формы приема на работу
Содержит формы для каждого шага визарда
"""
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, HTML, Button
from dal import autocomplete

from directory.models import Employee, Position, EmployeeHiring

# Форма для шага 1 - базовая информация
class Step1BasicInfoForm(forms.Form):
    """Базовые данные о сотруднике и должности"""
    # Ваш код для формы...
    pass

# Форма для шага 2 - медицинская информация
class Step2MedicalInfoForm(forms.Form):
    """Информация для медосмотра"""
    # Ваш код для формы...
    pass

# Форма для шага 3 - информация по СИЗ
class Step3SIZInfoForm(forms.Form):
    """Информация для СИЗ"""
    # Ваш код для формы...
    pass
'''
        },
        # Представления
        {
            'path': os.path.join(dirs['views'], 'hiring_wizard.py'),
            'content': '''# -*- coding: utf-8 -*-
"""
👨‍💼 Представления для многошаговой формы приема на работу
Использует FormWizard для реализации шагов
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from formtools.wizard.views import SessionWizardView

from directory.forms.hiring_wizard import Step1BasicInfoForm, Step2MedicalInfoForm, Step3SIZInfoForm
from directory.models import Employee, EmployeeHiring, Position

class HiringWizardView(LoginRequiredMixin, SessionWizardView):
    """Мастер формы для пошагового приема на работу"""
    # Ваш код для представления...
    pass
'''
        },
        # API
        {
            'path': os.path.join(dirs['views'], 'api.py'),
            'content': '''# -*- coding: utf-8 -*-
"""
🔌 API представления для взаимодействия с формой
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from directory.models import Position, MedicalExaminationNorm

@login_required
def position_needs_step_info(request, position_id):
    """
    API для получения информации о том, нужны ли дополнительные шаги
    для выбранной должности
    """
    # Ваш код для API...
    pass
'''
        },
        # Шаблон
        {
            'path': os.path.join(dirs['templates'], 'wizard_form.html'),
            'content': '''{% extends 'base.html' %}
{% load static %}
{% load crispy_forms_tags %}

{% block title %}{{ title }}{% endblock %}

{% block extra_css %}
<style>
    /* Стили для многошаговой формы */
</style>
{% endblock %}

{% block content %}
<div class="container">
    <h1 class="mt-4 mb-4">{{ title }}</h1>

    <!-- Шаги визарда -->
    <div class="wizard-steps">
        <!-- Ваш HTML-код для отображения шагов -->
    </div>

    <!-- Форма шага -->
    <div class="card">
        <!-- Ваш HTML-код для формы -->
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Ваш JavaScript для формы
</script>
{% endblock %}
'''
        },
        # URL маршруты (отдельный файл для подключения)
        {
            'path': os.path.join(base_dir, 'directory', 'urls_hiring_wizard.py'),
            'content': '''# -*- coding: utf-8 -*-
"""
🔗 URL-маршруты для многошаговой формы приема на работу
Добавьте это в основной urls.py
"""
from django.urls import path
from directory.views.hiring_wizard import HiringWizardView
from directory.views.api import position_needs_step_info

# URL-маршруты для многошаговой формы
urlpatterns = [
    # Многошаговая форма приема на работу
    path('hiring/wizard/', HiringWizardView.as_view(), name='hiring_wizard'),

    # API для проверки требуемых шагов
    path('api/position/<int:position_id>/needs_step_info/', 
         position_needs_step_info, 
         name='position_needs_step_info'),
]
'''
        },
    ]

    # Создаем файлы
    created_count = 0
    for file_info in files:
        if create_file(file_info['path'], file_info['content']):
            created_count += 1

    print(f"\n📋 Итого: Создано {created_count} файлов из {len(files)}")
    print("""
✨ Дальнейшие шаги:
1. Установите необходимые зависимости:
   pip install django-formtools

2. Наполните файлы кодом из предыдущего ответа

3. Подключите URL-маршруты в основной urls.py:
   from directory.urls_hiring_wizard import urlpatterns as hiring_wizard_urls
   urlpatterns += hiring_wizard_urls

4. Запустите миграции, если необходимо:
   python manage.py makemigrations
   python manage.py migrate
    """)


if __name__ == "__main__":
    main()