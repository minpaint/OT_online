#!/usr/bin/env python
"""
Скрипт для создания структуры файлов системы документов.

Запускайте этот скрипт из корневой директории проекта Django.
"""
import os
import sys
import shutil

# Проверка, что мы находимся в корректной директории
if not os.path.exists('manage.py'):
    print("Ошибка: Скрипт должен быть запущен из корневой директории проекта Django.")
    sys.exit(1)

# Определение папок и файлов
directories = [
    # Основные директории
    "directory/models",
    "directory/views",
    "directory/forms",
    "directory/utils",
    "directory/urls",
    "directory/admin",
    "directory/management/commands",
    "directory/data/templates",

    # Директории для шаблонов
    "directory/templates/directory/documents",
    "directory/templates/admin/directory",  # Добавляем директорию для административных шаблонов

    # Директории для статических файлов
    "static/directory/js",
    "static/directory/css",
]

files = [
    # Модели
    {
        "path": "directory/models/document_template.py",
        "description": "Модели для шаблонов документов и сгенерированных документов"
    },

    # Обновление инициализации моделей
    {
        "path": "directory/models/__init__.py",
        "description": "Инициализация моделей с импортом новой модели документов",
        "content": """from directory.models.employee import Employee
from directory.models.organization import Organization
from directory.models.position import Position
from directory.models.department import Department
from directory.models.subdivision import Subdivision
# Импортируем модели документов
from directory.models.document_template import DocumentTemplate, GeneratedDocument
"""
    },

    # Утилиты
    {
        "path": "directory/utils/declension.py",
        "description": "Утилиты для склонения слов с помощью pymorphy2"
    },
    {
        "path": "directory/utils/docx_generator.py",
        "description": "Утилиты для генерации документов на основе шаблонов"
    },

    # Представления
    {
        "path": "directory/views/documents.py",
        "description": "Представления для работы с документами"
    },

    # Формы
    {
        "path": "directory/forms/document_forms.py",
        "description": "Формы для работы с документами"
    },

    # URL-маршруты
    {
        "path": "directory/urls/documents.py",
        "description": "URL-маршруты для работы с документами"
    },

    # Обновление инициализации URL-маршрутов
    {
        "path": "directory/urls/__init__.py",
        "description": "Инициализация URL-маршрутов с импортом маршрутов документов"
    },

    # Административный интерфейс
    {
        "path": "directory/admin/document_admin.py",
        "description": "Административный интерфейс для моделей документов"
    },

    # Обновление инициализации админки
    {
        "path": "directory/admin/__init__.py",
        "description": "Инициализация админки с импортом админки документов",
        "content": """from directory.admin.employee_admin import EmployeeAdmin
from directory.admin.organization_admin import OrganizationAdmin
from directory.admin.position_admin import PositionAdmin
from directory.admin.department_admin import DepartmentAdmin
from directory.admin.subdivision_admin import SubdivisionAdmin
# Импортируем админку документов
from directory.admin.document_admin import DocumentTemplateAdmin, GeneratedDocumentAdmin
"""
    },

    # Команда для инициализации шаблонов
    {
        "path": "directory/management/commands/init_document_templates.py",
        "description": "Команда для инициализации шаблонов документов"
    },

    # Шаблоны HTML
    {
        "path": "directory/templates/directory/documents/document_selection.html",
        "description": "Шаблон для выбора типа документа"
    },
    {
        "path": "directory/templates/directory/documents/internship_order_form.html",
        "description": "Шаблон для формы распоряжения о стажировке"
    },
    {
        "path": "directory/templates/directory/documents/admission_order_form.html",
        "description": "Шаблон для формы распоряжения о допуске к самостоятельной работе"
    },
    {
        "path": "directory/templates/directory/documents/document_preview.html",
        "description": "Шаблон для предпросмотра документа"
    },
    {
        "path": "directory/templates/directory/documents/document_detail.html",
        "description": "Шаблон для просмотра деталей документа"
    },
    {
        "path": "directory/templates/directory/documents/document_list.html",
        "description": "Шаблон для списка сгенерированных документов"
    },

    # JavaScript
    {
        "path": "static/directory/js/employee_tree_documents.js",
        "description": "JavaScript для обработки выбора сотрудников и запуска генерации документов"
    },

    # Обновление шаблона дерева сотрудников (с проверкой существования оригинального файла)
    {
        "path": "directory/templates/admin/directory/employee_tree_list.html",
        "description": "Обновление шаблона дерева сотрудников с добавлением кнопки генерации документов",
        "check_exist": True,  # Проверка существования оригинального файла
        "content": """{% extends "admin/base_site.html" %}
{% load i18n static %}

{% block extrahead %}
    {{ block.super }}
    <script src="{% static 'directory/js/employee_tree_documents.js' %}"></script>
{% endblock %}

{% block object-tools %}
  <!-- Кнопка для добавления нового сотрудника -->
  <div class="object-tools">
    <ul class="object-tools">
      <li>
        <a href="{% url 'admin:directory_employee_add' %}" class="addlink">➕ Добавить сотрудника</a>
      </li>
      <li>
        <a href="#" id="generate-documents-btn" class="btn" style="display: none;">📄 Сгенерировать документы</a>
      </li>
    </ul>
  </div>
{% endblock %}

{% block content %}
  <h1>👥 Дерево сотрудников</h1>
  <ul>
    {% for organization, org_group in employee_tree.items %}
      <li>
        <strong>🏢 {{ organization.full_name_ru }}</strong>
        <ul>
          {% for subdivision, sub_group in org_group.items %}
            <li>
              {% if subdivision == "Без подразделения" %}
                <em>Без подразделения</em>
              {% else %}
                🏭 {{ subdivision.name }}
              {% endif %}
              <ul>
                {% for department, employees in sub_group.items %}
                  <li>
                    {% if department == "Без отдела" %}
                      <em>Без отдела</em>
                    {% else %}
                      📂 {{ department.name }}
                    {% endif %}
                    <ul>
                      {% for employee in employees %}
                        <li>
                          <input type="checkbox" class="action-select" value="{{ employee.id }}">
                          👤 {{ employee.full_name_nominative }} – {{ employee.position.position_name }}
                        </li>
                      {% endfor %}
                    </ul>
                  </li>
                {% endfor %}
              </ul>
            </li>
          {% endfor %}
        </ul>
      </li>
    {% endfor %}
  </ul>
{% endblock %}"""
    },

    # Документация
    {
        "path": "directory/data/document_templates_instructions.md",
        "description": "Инструкции по созданию шаблонов DOCX"
    },
    {
        "path": "directory/data/documents_user_guide.md",
        "description": "Руководство пользователя по генерации документов"
    },
]


# Функция для создания директорий
def create_directories():
    print("Создание директорий...")
    for directory in directories:
        path = os.path.join(os.getcwd(), directory)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Создана директория: {path}")
        else:
            print(f"Директория уже существует: {path}")


# Функция для создания файлов
def create_files():
    print("\nСоздание файлов...")
    for file_info in files:
        path = os.path.join(os.getcwd(), file_info["path"])

        # Проверяем существование файла и директории
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Создана директория: {directory}")

        # Если указано проверять существование файла и файл не существует, пропускаем
        if file_info.get("check_exist", False) and not os.path.exists(path):
            print(f"Файл не существует, необходимо создать вручную: {path}")
            # Создаем пустой файл с содержимым, если оно указано
            if "content" in file_info:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
                print(f"Создан шаблон файла с базовым содержимым: {path}")
            continue

        # Если файл уже существует, создаем резервную копию
        if os.path.exists(path):
            backup_path = path + ".bak"
            if not os.path.exists(backup_path):
                shutil.copy2(path, backup_path)
                print(f"Создана резервная копия: {backup_path}")

        # Создаем файл
        with open(path, 'w', encoding='utf-8') as f:
            # Если есть указанное содержимое, используем его
            if "content" in file_info:
                f.write(file_info["content"])
            else:
                # Иначе добавляем заглушку с описанием
                f.write(f'"""\n{file_info["description"]}\n"""\n\n# Заполните этот файл кодом\n')

        print(f"Создан файл: {path}")


# Создание пустых файлов __init__.py
def create_init_files():
    print("\nСоздание файлов инициализации...")
    for directory in directories:
        if directory.startswith('directory') and not directory.endswith('templates') and not directory.endswith(
                'directory'):
            init_path = os.path.join(os.getcwd(), directory, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, 'w', encoding='utf-8') as f:
                    f.write('"""\nИнициализация модуля.\n"""\n')
                print(f"Создан файл инициализации: {init_path}")


# Основная функция
def main():
    print("Начало создания структуры файлов для системы документов...")

    # Создаем директории
    create_directories()

    # Создаем файлы
    create_files()

    # Создаем файлы инициализации
    create_init_files()

    print("\nСтруктура файлов успешно создана!")
    print("\nДля установки необходимых зависимостей выполните:")
    print("pip install pymorphy2 docxtpl\n")


if __name__ == "__main__":
    main()