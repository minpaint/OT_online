#!/usr/bin/env python3
"""
🚀 Скрипт для автоматического создания шаблонов древовидного отображения.
Для каждой модели (employee, equipment, document, department, subdivision, position)
будет создан файл:
    templates/admin/directory/<model>/change_list_tree.html
с базовой разметкой, аналогичной шаблону для Position.
"""

import os

# Список моделей, для которых нужно создать шаблоны (Organization не включаем)
models = ["employee", "equipment", "document", "department", "subdivision", "position"]

# Базовая директория для шаблонов
base_dir = os.path.join("templates", "admin", "directory")

# Базовый контент шаблона с placeholder {{ model_name }}
# Этот код аналогичен вашему шаблону для Position, но с автоматической подстановкой имени модели.
template_content = """{% extends "admin/change_list.html" %}
{% load static %}

{% block content %}
<div id="content-main">
    <form id="changelist-form" method="post"
          {% if cl.formset and cl.formset.is_multipart %} enctype="multipart/form-data"{% endif %}
          novalidate>
        {% csrf_token %}
        {% if action_form and actions_on_top and cl.show_admin_actions %}
            <div class="actions">
                {% for field in action_form %}
                    {% if field.label %}<label>{{ field.label }}</label>{% endif %}
                    {{ field }}
                {% endfor %}
                <button type="submit" class="button" title="Выполнить выбранное действие">Выполнить</button>
                <span class="action-counter" style="display: none;">0 из {{ cl.result_count }} выбрано</span>
            </div>
        {% endif %}

        <div class="tree-controls">
            <button type="button" class="tree-btn expand-all">↓ Развернуть все</button>
            <button type="button" class="tree-btn collapse-all">↑ Свернуть все</button>
            <div class="tree-search-container">
                <input type="text" class="tree-search" placeholder="🔍 Поиск по дереву...">
            </div>
        </div>

        <div class="results">
            <table id="result_list">
                <thead>
                    <tr>
                        <th class="column-checkbox"><input type="checkbox" id="select-all"></th>
                        <th class="column-name">НАИМЕНОВАНИЕ</th>
                        <th class="column-roles">АТРИБУТЫ/РОЛИ</th>
                        <th class="column-actions">ДЕЙСТВИЯ</th>
                    </tr>
                </thead>
                <tbody>
                    {% for org, org_data in tree.items %}
                    <tr class="tree-row" data-level="0" data-node-id="org_{{ org.id }}">
                        <td class="field-checkbox"></td>
                        <td class="field-name">
                            <button type="button" class="toggle-btn" data-state="expanded">[-]</button>
                            <span class="tree-icon">{{ tree_settings.icons.organization }}</span>
                            <strong>{{ org_data.name }}</strong>
                        </td>
                        <td class="field-roles"></td>
                        <td class="field-actions"></td>
                    </tr>

                    {# Элементы без subdivision #}
                    {% for item in org_data.items %}
                    <tr class="tree-row" data-level="1" data-parent-id="org_{{ org.id }}">
                        <td class="field-checkbox">
                            <input type="checkbox" name="_selected_action" value="{{ item.object.pk }}" class="action-select">
                        </td>
                        <td class="field-name">
                            <span class="tree-icon">{{ tree_settings.icons.item }}</span>
                            <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}">
                                {{ item.name }}
                            </a>
                        </td>
                        <td class="field-roles"></td>
                        <td class="field-actions">
                            <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}" class="edit-link">✏️</a>
                            <a href="{% url 'admin:directory_{{ model_name }}_delete' item.object.pk %}" class="delete-link">🗑️</a>
                            <a href="{% url 'admin:directory_{{ model_name }}_history' item.object.pk %}" class="history-link">📋</a>
                        </td>
                    </tr>
                    {% endfor %}

                    {# Подразделения #}
                    {% for sub, sub_data in org_data.subdivisions.items %}
                    <tr class="tree-row" data-level="1" data-parent-id="org_{{ org.id }}" data-node-id="sub_{{ sub.id }}">
                        <td class="field-checkbox"></td>
                        <td class="field-name">
                            <button type="button" class="toggle-btn" data-state="expanded">[-]</button>
                            <span class="tree-icon">{{ tree_settings.icons.subdivision }}</span>
                            {{ sub_data.name }}
                        </td>
                        <td class="field-roles"></td>
                        <td class="field-actions"></td>
                    </tr>

                        {# Элементы без department #}
                        {% for item in sub_data.items %}
                        <tr class="tree-row" data-level="2" data-parent-id="sub_{{ sub.id }}">
                            <td class="field-checkbox">
                                <input type="checkbox" name="_selected_action" value="{{ item.object.pk }}" class="action-select">
                            </td>
                            <td class="field-name">
                                <span class="tree-icon">{{ tree_settings.icons.item }}</span>
                                <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}">
                                    {{ item.name }}
                                </a>
                            </td>
                            <td class="field-roles"></td>
                            <td class="field-actions">
                                <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}" class="edit-link">✏️</a>
                                <a href="{% url 'admin:directory_{{ model_name }}_delete' item.object.pk %}" class="delete-link">🗑️</a>
                                <a href="{% url 'admin:directory_{{ model_name }}_history' item.object.pk %}" class="history-link">📋</a>
                            </td>
                        </tr>
                        {% endfor %}

                        {# Отделы #}
                        {% for dept, dept_data in sub_data.departments.items %}
                        <tr class="tree-row" data-level="2" data-parent-id="sub_{{ sub.id }}" data-node-id="dept_{{ dept.id }}">
                            <td class="field-checkbox"></td>
                            <td class="field-name">
                                <button type="button" class="toggle-btn" data-state="expanded">[-]</button>
                                <span class="tree-icon">{{ tree_settings.icons.department }}</span>
                                {{ dept_data.name }}
                            </td>
                            <td class="field-roles"></td>
                            <td class="field-actions"></td>
                        </tr>

                        {% for item in dept_data.items %}
                        <tr class="tree-row" data-level="3" data-parent-id="dept_{{ dept.id }}">
                            <td class="field-checkbox">
                                <input type="checkbox" name="_selected_action" value="{{ item.object.pk }}" class="action-select">
                            </td>
                            <td class="field-name">
                                <span class="tree-icon">{{ tree_settings.icons.item }}</span>
                                <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}">
                                    {{ item.name }}
                                </a>
                            </td>
                            <td class="field-roles"></td>
                            <td class="field-actions">
                                <a href="{% url 'admin:directory_{{ model_name }}_change' item.object.pk %}" class="edit-link">✏️</a>
                                <a href="{% url 'admin:directory_{{ model_name }}_delete' item.object.pk %}" class="delete-link">🗑️</a>
                                <a href="{% url 'admin:directory_{{ model_name }}_history' item.object.pk %}" class="history-link">📋</a>
                            </td>
                        </tr>
                        {% endfor %}
                        {% endfor %}
                    {% endfor %}
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </form>
</div>
{% endblock %}

{% block extrahead %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'admin/css/tree_view.css' %}">
    <script src="{% static 'admin/js/tree_view.js' %}"></script>
    <script src="{% static 'admin/js/tree_search.js' %}"></script>
{% endblock %}
"""


def create_template_file(model_name):
    # Определяем целевую директорию для шаблона
    target_dir = os.path.join(base_dir, model_name)
    os.makedirs(target_dir, exist_ok=True)

    # Путь к файлу change_list_tree.html
    target_file = os.path.join(target_dir, "change_list_tree.html")

    # Заменяем placeholder {{ model_name }} на текущее имя модели
    content = template_content.replace("{{ model_name }}", model_name)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Шаблон для модели '{model_name}' создан: {target_file}")


def main():
    print("🚀 Запуск скрипта создания шаблонов для древовидного отображения...")
    for model in models:
        create_template_file(model)
    print("🎉 Все шаблоны успешно созданы!")


if __name__ == "__main__":
    main()
