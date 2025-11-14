# Руководство по разработке: Единый импорт справочников

## 1. Цель

Реализовать функционал для массового импорта ключевых справочников (`Структура`, `Сотрудники`, `СИЗ`, `Оборудование` и др.) из одного Excel-файла. Пользователь должен иметь возможность выбрать организацию, загрузить файл, после чего система атомарно импортирует данные из каждого листа файла в соответствующий справочник.

## 2. Структура Excel-файла

Файл должен содержать несколько листов. Имена листов должны быть строго стандартизированы. Порядок листов в файле не важен, так как логика импорта будет сама определять правильную последовательность обработки.

### Обязательные имена листов и порядок обработки:

1.  `Структура` - организационная структура (подразделения, отделы, должности).
2.  `Сотрудники` - сотрудники.
3.  `СИЗ` - номенклатура СИЗ.
4.  `Оборудование` - оборудование.

### Структура колонок

Колонки в каждом листе должны соответствовать полям, определённым в соответствующих классах `Resource` (`directory/resources/`).

**Пример для листа `Структура`:**
(`OrganizationStructureResource`)

| org_short_name_ru | subdivision_name | department_name | position_name | category |
| ----------------- | ---------------- | --------------- | ------------- | -------- |
| ООО "Ромашка"     | Администрация    | Отдел кадров    | Инспектор     |          |
| ООО "Ромашка"     | Производство     | Цех №1          | Токарь        | Рабочий  |

**Пример для листа `Сотрудники`:**
(`EmployeeResource`)

| last_name | first_name | patronymic | position_name | department_name | subdivision_name | personnel_number |
| --------- | ---------- | ---------- | ------------- | --------------- | ---------------- | ---------------- |
| Иванов    | Иван       | Иванович   | Инспектор     | Отдел кадров    | Администрация    | 101              |
| Петров    | Петр       | Петрович   | Токарь        | Цех №1          | Производство     | 102              |

## 3. План реализации

### Шаг 1: Создание URL и View

1.  **Создать View:**
    В файле `directory/views.py` (или в новом файле, например `directory/views/import_views.py`) создать `GlobalImportView`. Эта View будет обрабатывать GET-запросы (отображение формы) и POST-запросы (обработка файла).

2.  **Создать URL:**
    В файле `directory/urls.py` добавить новый путь:
    ```python
    # directory/urls.py
    from .views import GlobalImportView # (предполагая, что view в views.py)

    urlpatterns = [
        # ... другие пути
        path('import/global/', GlobalImportView.as_view(), name='global_import'),
    ]
    ```

### Шаг 2: Форма и HTML-шаблон

1.  **Создать форму:**
    В новом файле `directory/forms/import_forms.py` создать форму для загрузки файла и выбора организации.

    ```python
    # directory/forms/import_forms.py
    from django import forms
    from ..models import Organization

    class GlobalImportForm(forms.Form):
        organization = forms.ModelChoiceField(
            queryset=Organization.objects.all(),
            label="Организация для импорта",
            required=True
        )
        file = forms.FileField(
            label="Excel-файл (.xlsx)",
            required=True,
            widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'})
        )
    ```

2.  **Создать HTML-шаблон:**
    Создать файл `directory/templates/directory/global_import.html`.

    ```html
    {% extends "base.html" %}
    {% block content %}
    <h2>Единый импорт справочников</h2>
    <p>Загрузите Excel-файл (.xlsx) со стандартизированными именами листов ('Структура', 'Сотрудники' и т.д.) для импорта данных в выбранную организацию.</p>
    
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Начать импорт</button>
    </form>
    
    {% if results %}
        <h3>Результаты импорта</h3>
        {% for result in results %}
            <h4>Лист: {{ result.sheet_name }}</h4>
            <p>Статус: {{ result.status }}</p>
            {% if result.errors %}
                <ul>
                {% for error in result.errors %}
                    <li>Строка {{ error.row_number }}: {{ error.error_message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endfor %}
    {% endif %}
    {% endblock %}
    ```

### Шаг 3: Реализация View

```python
# directory/views.py
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from .forms import GlobalImportForm
from .services import run_global_import # Сервис будет создан на следующем шаге

class GlobalImportView(View):
    form_class = GlobalImportForm
    template_name = 'directory/global_import.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            organization = form.cleaned_data['organization']
            file = request.FILES['file']
            
            try:
                results = run_global_import(file, organization)
                # Отобразить детальные результаты на странице
                return render(request, self.template_name, {'form': form, 'results': results})
            except Exception as e:
                messages.error(request, f"Произошла критическая ошибка: {e}")

        return render(request, self.template_name, {'form': form})

```

### Шаг 4: Создание сервиса-оркестратора

Это ядро функционала. Создать новый файл `directory/services.py`.

1.  **Установить `pandas` и `openpyxl`**:
    `pip install pandas openpyxl`
    Добавить их в `requirements.txt`.

2.  **Адаптировать существующие `Resource`**:
    Нужно иметь возможность передавать `organization` в `Resource`. Можно создать базовый класс-миксин.

    ```python
    # directory/resources/mixins.py (новый файл)
    class OrganizationResourceMixin:
        def __init__(self, organization=None, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.organization = organization

        def before_import_row(self, row, **kwargs):
            # Переопределяем логику, чтобы она использовала self.organization
            # вместо request.user.organization
            if self.organization:
                row['org_short_name_ru'] = self.organization.short_name_ru
            # ... остальная логика из существующих before_import_row
    ```
    Затем унаследовать `OrganizationStructureResource`, `EmployeeResource` и др. от этого миксина.

3.  **Написать оркестратор `run_global_import`**:

    ```python
    # directory/services.py
    import pandas as pd
    from tablib import Dataset
    from django.db import transaction

    from .models import Organization
    from .resources import (
        OrganizationStructureResource, 
        EmployeeResource, 
        # ... импортировать другие адаптированные ресурсы
    )

    # Словарь для сопоставления имен листов и ресурсов
    RESOURCE_MAPPING = {
        'Структура': OrganizationStructureResource,
        'Сотрудники': EmployeeResource,
        # ... другие
    }
    
    # Порядок обработки
    PROCESSING_ORDER = ['Структура', 'Сотрудники', 'СИЗ', 'Оборудование']

    @transaction.atomic
    def run_global_import(file_obj, organization: Organization):
        """
        Оркестратор импорта из Excel-файла.
        """
        try:
            xls = pd.ExcelFile(file_obj)
        except Exception as e:
            raise ValueError(f"Не удалось прочитать Excel-файл. Ошибка: {e}")

        sheet_names = xls.sheet_names
        results = []
        
        # Сортируем листы в правильном порядке
        sorted_sheets = [name for name in PROCESSING_ORDER if name in sheet_names]

        for sheet_name in sorted_sheets:
            if sheet_name not in RESOURCE_MAPPING:
                continue

            df = pd.read_excel(xls, sheet_name=sheet_name).fillna('')
            dataset = Dataset().load(df.to_csv(index=False), format='csv')
            
            # Создаем ресурс, передавая организацию
            resource_class = RESOURCE_MAPPING[sheet_name]
            resource = resource_class(organization=organization)
            
            result = resource.import_data(dataset, dry_run=False, raise_errors=False)
            
            sheet_result = {
                "sheet_name": sheet_name,
                "status": "Успешно" if not result.has_errors() else "Есть ошибки",
                "errors": []
            }

            if result.has_errors():
                for error in result.row_errors():
                    sheet_result["errors"].append({
                        "row_number": error[0],
                        "error_message": str(error[1][0].error)
                    })
            
            results.append(sheet_result)

            # Если в критически важном листе (Структура) есть ошибки, прерываем транзакцию
            if sheet_name == 'Структура' and result.has_errors():
                raise ValueError(f"Импорт остановлен. Обнаружены ошибки в листе 'Структура'.")

        return results
    ```

## 4. Заключительные шаги

1.  **Добавить зависимости**: Убедиться, что `pandas` и `openpyxl` добавлены в `requirements.txt`.
2.  **Миграции**: Если были изменения в моделях (маловероятно), создать и применить миграции.
3.  **Тестирование**: Тщательно протестировать функционал с разными сценариями:
    *   Корректный файл.
    *   Файл с ошибками в данных (например, несуществующий отдел для сотрудника).
    *   Файл с неправильными именами листов.
    *   Прерывание импорта после ошибок в листе "Структура".
4.  **Документация**: Обновить пользовательскую документацию, описав новый функционал и требования к Excel-файлу.
