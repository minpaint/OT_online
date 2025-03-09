#!/usr/bin/env python
"""
Скрипт для создания фронтенд-файлов для древовидного списка сотрудников
в репозитории minpaint/OT_online
"""

import os
import sys


def create_directory(directory_path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Создана директория {directory_path}")


def create_file(file_path, content):
    """Создает файл с указанным содержимым"""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Создан файл {file_path}")


# Содержимое frontend_tree_view.js
frontend_tree_view_js = '''/**
 * 🌳 Ядро древовидного списка для фронтенда
 * Управляет деревом сотрудников с поведением радиокнопок
 */
class EmployeeTreeCore {
    constructor() {
        // 🎯 Основные элементы фронтенда
        this.tree = document.getElementById('employeeTree');
        this.expandAllBtn = document.querySelector('.expand-all');
        this.collapseAllBtn = document.querySelector('.collapse-all');
        this.searchInput = document.getElementById('localSearchInput');
        this.selectAllCheckbox = document.getElementById('select-all');

        // 👥 Элементы для работы с выбранными сотрудниками
        this.actionsDropdown = document.getElementById('actionsDropdown');
        this.selectedCounter = document.getElementById('selectedCounter');
        this.counterValue = document.getElementById('counterValue');
        this.selectedCountBadge = document.getElementById('selectedCount');

        // ID выбранного сотрудника (для поведения радиокнопок)
        this.selectedEmployee = null;

        // Защита от многократной инициализации
        if (window._treeInitialized) {
            console.warn('EmployeeTreeCore уже инициализирован');
            return;
        }
        window._treeInitialized = true;

        // Инициализация
        this.init();
    }

    init() {
        if (!this.tree) return;
        this._bindEvents();
        this._restoreState();
        this._initCheckboxes();
        this._initEmployeeActions();

        // Синхронизируем начальное состояние счетчика
        this._syncInitialState();
    }

    _syncInitialState() {
        // Находим текущий выбранный чекбокс сотрудника
        const checkedEmployee = this.tree.querySelector('.employee-checkbox:checked');
        if (checkedEmployee) {
            this.selectedEmployee = checkedEmployee.dataset.id;
        }

        // Форсированно обновляем счетчик
        this._updateSelectedCounter();
    }

    _bindEvents() {
        // Делегирование кликов в таблице для фронтенда использует tree-toggle
        this.tree.addEventListener('click', (e) => {
            if (e.target.classList.contains('tree-toggle')) {
                this._handleToggleClick(e);
            }
        });

        if (this.expandAllBtn) {
            this.expandAllBtn.addEventListener('click', () => this.expandAll());
        }
        if (this.collapseAllBtn) {
            this.collapseAllBtn.addEventListener('click', () => this.collapseAll());
        }

        // Добавляем доступность с клавиатуры
        this._addKeyboardSupport();
    }

    _addKeyboardSupport() {
        const toggleElements = this.tree.querySelectorAll('.tree-toggle');
        toggleElements.forEach(toggle => {
            toggle.setAttribute('tabindex', '0');

            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this._handleToggleClick({ target: toggle });
                }
            });
        });
    }

    _handleToggleClick(event) {
        const toggleElement = event.target;
        if (!toggleElement.classList.contains('tree-toggle')) return;

        const nodeId = toggleElement.dataset.node;
        if (!nodeId) return;

        const isExpanded = toggleElement.textContent === '-';
        this.toggleNodeByToggleIcon(nodeId, !isExpanded);
    }

    toggleNodeByToggleIcon(nodeId, expand = true) {
        const toggleElement = this.tree.querySelector(`.tree-toggle[data-node="${nodeId}"]`);
        if (!toggleElement) return;

        toggleElement.textContent = expand ? '-' : '+';

        const children = this.tree.querySelectorAll(`tr[data-parent="${nodeId}"]`);
        children.forEach(child => {
            if (expand) {
                child.classList.remove('tree-hidden');
            } else {
                child.classList.add('tree-hidden');

                // Проверяем, есть ли у ребенка свои дети
                const childNodeId = child.dataset.nodeId;
                if (childNodeId) {
                    this.toggleNodeByToggleIcon(childNodeId, false);
                }
            }
        });

        this._saveState();
    }

    expandAll() {
        const toggles = this.tree.querySelectorAll('.tree-toggle');
        toggles.forEach(toggle => {
            const nodeId = toggle.dataset.node;
            if (nodeId) {
                this.toggleNodeByToggleIcon(nodeId, true);
            }
        });
    }

    collapseAll() {
        // Сворачиваем только корневые элементы (организации)
        const orgNodes = this.tree.querySelectorAll('.tree-toggle[data-node^="org-"]');
        orgNodes.forEach(node => {
            const nodeId = node.dataset.node;
            this.toggleNodeByToggleIcon(nodeId, false);
        });
    }

    _saveState() {
        try {
            const state = {};
            const toggles = this.tree.querySelectorAll('.tree-toggle');
            toggles.forEach(toggle => {
                const nodeId = toggle.dataset.node;
                if (nodeId) {
                    state[nodeId] = toggle.textContent === '-' ? 'expanded' : 'collapsed';
                }
            });
            localStorage.setItem('employeeTreeState', JSON.stringify(state));
        } catch (e) {
            console.error('Ошибка сохранения состояния дерева:', e);
        }
    }

    _restoreState() {
        try {
            const state = JSON.parse(localStorage.getItem('employeeTreeState'));
            if (state) {
                Object.entries(state).forEach(([nodeId, st]) => {
                    this.toggleNodeByToggleIcon(nodeId, st === 'expanded');
                });
            }
        } catch (err) {
            console.error('Ошибка восстановления состояния дерева:', err);
        }
    }

    _initCheckboxes() {
        // Для фронтенда скрываем чекбокс "выбрать всё" - нужен только один выбор
        if (this.selectAllCheckbox) {
            this.selectAllCheckbox.style.display = 'none';
        }

        // Используем делегирование событий вместо множества обработчиков
        this.tree.addEventListener('change', this._handleCheckboxChange.bind(this));
    }

    _handleCheckboxChange(event) {
        const checkbox = event.target;
        if (!checkbox.matches('input[type="checkbox"]')) return;

        // Обрабатываем только чекбоксы сотрудников
        if (checkbox.classList.contains('employee-checkbox')) {
            if (checkbox.checked) {
                // Снимаем все остальные чекбоксы (поведение радиокнопок)
                const allCheckboxes = this.tree.querySelectorAll('.employee-checkbox');
                allCheckboxes.forEach(cb => {
                    if (cb !== checkbox && cb.checked) {
                        cb.checked = false;
                    }
                });

                // Запоминаем ID выбранного сотрудника
                this.selectedEmployee = checkbox.dataset.id;

                // Визуально подсвечиваем выбранную строку
                const allRows = this.tree.querySelectorAll('tr.tree-row');
                allRows.forEach(row => row.classList.remove('selected-row'));
                checkbox.closest('tr').classList.add('selected-row');
            } else {
                // Если сняли чекбокс - очищаем выбор
                this.selectedEmployee = null;
                checkbox.closest('tr').classList.remove('selected-row');
            }

            // Обновляем счетчик и состояние кнопок
            this._updateSelectedCounter();
        }
    }

    _updateSelectedCounter() {
        // Простой подсчет: 1 если есть выбранный сотрудник, иначе 0
        const count = this.selectedEmployee ? 1 : 0;

        // Обновляем счетчик в разных местах интерфейса
        if (this.counterValue) {
            this.counterValue.textContent = count;
        }

        if (this.selectedCounter) {
            this.selectedCounter.style.display = count > 0 ? 'inline-block' : 'none';
        }

        if (this.actionsDropdown) {
            this.actionsDropdown.disabled = count === 0;
        }

        // Обновляем счетчик в дропдауне
        if (this.selectedCountBadge) {
            this.selectedCountBadge.textContent = count;
        }

        // Обновляем состояние кнопок действий
        this._updateActionButtonsState();
    }

    _updateActionButtonsState() {
        // Получаем все кнопки действий
        const actionButtons = [
            document.getElementById('btnIssueCard'),
            document.getElementById('btnIssueSIZ'),
            document.getElementById('btnEditEmployee')
        ];

        // Обновляем их состояние
        actionButtons.forEach(btn => {
            if (btn) {
                btn.classList.toggle('disabled', !this.selectedEmployee);

                if (this.selectedEmployee) {
                    btn.removeAttribute('disabled');
                } else {
                    btn.setAttribute('disabled', 'disabled');
                }
            }
        });
    }

    /**
     * 🔄 Инициализация действий с сотрудниками
     */
    _initEmployeeActions() {
        // Инициализация кнопок действий
        const btnIssueCard = document.getElementById('btnIssueCard');
        const btnIssueSIZ = document.getElementById('btnIssueSIZ');
        const btnEditEmployee = document.getElementById('btnEditEmployee');

        if (btnIssueCard) {
            btnIssueCard.addEventListener('click', () => {
                if (!this.selectedEmployee) {
                    alert('Пожалуйста, выберите сотрудника для просмотра карточки учета.');
                    return;
                }

                // Переходим на страницу карточки учета выбранного сотрудника
                const employeeId = this.selectedEmployee;
                const url = document.querySelector('[data-siz-personal-card-url]')?.dataset.sizPersonalCardUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }

        if (btnIssueSIZ) {
            btnIssueSIZ.addEventListener('click', () => {
                if (!this.selectedEmployee) {
                    alert('Пожалуйста, выберите сотрудника для выдачи СИЗ.');
                    return;
                }

                // Формируем URL с параметром выбранного сотрудника
                const employeeId = this.selectedEmployee;
                const url = document.querySelector('[data-siz-issue-url]')?.dataset.sizIssueUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }

        if (btnEditEmployee) {
            btnEditEmployee.addEventListener('click', () => {
                if (!this.selectedEmployee) {
                    alert('Пожалуйста, выберите сотрудника для редактирования.');
                    return;
                }

                // Переходим на страницу редактирования выбранного сотрудника
                const employeeId = this.selectedEmployee;
                const url = document.querySelector('[data-employee-update-url]')?.dataset.employeeUpdateUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }
    }
}

// Автоинициализация для фронтенда
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, что мы находимся во фронтенде
    if (document.getElementById('employeeTree')) {
        window.employeeTreeCore = new EmployeeTreeCore();
    }
});
'''

# Содержимое frontend_tree_search.js
frontend_tree_search_js = '''/**
 * 🔍 Модуль поиска для древовидного списка сотрудников на фронтенде
 */
class EmployeeTreeSearch {
    constructor() {
        this.tree = document.getElementById('employeeTree');
        this.searchInput = document.getElementById('localSearchInput');
        this.searchBtn = document.getElementById('localSearchBtn');
        this.clearSearchBtn = document.getElementById('clearSearchBtn');

        this.debounceTimer = null;
        this.lastSearchTerm = '';

        this.init();
    }

    init() {
        if (!this.tree || !this.searchInput) return;

        // Обработчики событий для поиска
        this.searchInput.addEventListener('input', this._debounceSearch.bind(this));

        if (this.searchBtn) {
            this.searchBtn.addEventListener('click', () => {
                this._performSearch(this.searchInput.value);
            });
        }

        if (this.clearSearchBtn) {
            this.clearSearchBtn.addEventListener('click', () => {
                this._clearSearch();
            });
        }

        // Поиск по Enter и очистка по Escape
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this._performSearch(this.searchInput.value);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this._clearSearch();
            }
        });
    }

    _debounceSearch() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            const query = this.searchInput.value;
            if (query !== this.lastSearchTerm) {
                this._performSearch(query);
            }
        }, 300);
    }

    _performSearch(searchText) {
        searchText = searchText.toLowerCase().trim();

        // Если запрос пустой - сбрасываем поиск
        if (!searchText) {
            this._clearSearch();
            return;
        }

        this.lastSearchTerm = searchText;

        // Сначала все скрываем и убираем подсветку
        const allRows = this.tree.querySelectorAll('tr.tree-row');
        allRows.forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Ищем совпадения в тексте строк
        let foundCount = 0;
        allRows.forEach(row => {
            const text = row.textContent.toLowerCase();

            if (text.includes(searchText)) {
                // Строка содержит искомый текст
                row.classList.remove('hidden-by-search');

                // Подсвечиваем только строки сотрудников
                if (row.querySelector('.employee-checkbox')) {
                    row.classList.add('highlight-search');
                    foundCount++;
                }

                // Разворачиваем родительские узлы
                this._expandParentNodes(row);
            }
        });

        // Показываем сообщение с результатами
        if (foundCount > 0) {
            this._showSearchResult(`Найдено: ${foundCount}`);
        } else {
            this._showSearchResult('Ничего не найдено');
        }
    }

    _expandParentNodes(row) {
        const parentId = row.dataset.parent;
        if (!parentId) return;

        // Находим родительскую строку
        const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
        if (parentRow) {
            // Убираем скрытие с родителя
            parentRow.classList.remove('hidden-by-search');

            // Разворачиваем родителя
            const toggleIcon = parentRow.querySelector('.tree-toggle');
            if (toggleIcon && toggleIcon.textContent === '+') {
                if (window.employeeTreeCore) {
                    window.employeeTreeCore.toggleNodeByToggleIcon(parentId, true);
                } else {
                    toggleIcon.textContent = '-';

                    // Показываем все дочерние элементы
                    const children = this.tree.querySelectorAll(`tr[data-parent="${parentId}"]`);
                    children.forEach(child => child.classList.remove('tree-hidden'));
                }
            }

            // Рекурсивно обрабатываем родителей верхнего уровня
            this._expandParentNodes(parentRow);
        }
    }

    _showSearchResult(message) {
        // Показываем результат поиска (можно расширить для более красивого UI)
        const searchResultElement = document.querySelector('.search-results');
        if (searchResultElement) {
            searchResultElement.textContent = message;
            searchResultElement.style.display = 'block';
        } else {
            // Если элемента нет, показываем сообщение возле поиска
            const searchContainer = this.searchInput.closest('.card-body');
            if (searchContainer) {
                let resultElement = searchContainer.querySelector('.search-results');
                if (!resultElement) {
                    resultElement = document.createElement('div');
                    resultElement.className = 'search-results mt-2';
                    searchContainer.appendChild(resultElement);
                }
                resultElement.textContent = message;
            }
        }
    }

    _clearSearch() {
        // Очищаем поле поиска
        if (this.searchInput) {
            this.searchInput.value = '';
        }

        this.lastSearchTerm = '';

        // Убираем скрытие и подсветку со всех строк
        const allRows = this.tree.querySelectorAll('tr.tree-row');
        allRows.forEach(row => {
            row.classList.remove('hidden-by-search', 'highlight-search');
        });

        // Скрываем сообщение с результатами
        const searchResultElement = document.querySelector('.search-results');
        if (searchResultElement) {
            searchResultElement.textContent = '';
            searchResultElement.style.display = 'none';
        }

        // Возвращаем фокус на поле поиска
        if (this.searchInput) {
            this.searchInput.focus();
        }
    }
}

// Инициализация для фронтенда
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, что мы во фронтенде
    if (document.getElementById('employeeTree')) {
        window.employeeTreeSearch = new EmployeeTreeSearch();
    }
});
'''

# Содержимое frontend_tree_view.css
frontend_tree_view_css = '''/*
 * ========== frontend_tree_view.css ==========
 * Стили для древовидной таблицы сотрудников во фронтенде
 */

/* Основная таблица для дерева сотрудников */
.tree-table {
    width: 100%;
    margin: 0;
    border-collapse: collapse;
}

/* Стили для чекбоксов */
.employee-checkbox {
    cursor: pointer;
    width: 18px;
    height: 18px;
    vertical-align: middle;
    transition: transform 0.2s ease;
}

.employee-checkbox:hover {
    transform: scale(1.2);
}

.employee-checkbox:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

/* Отступы для уровней во фронтенде */
.tree-level {
    padding-left: 15px;
}
.tree-level-2 {
    padding-left: 30px;
}
.tree-level-3 {
    padding-left: 45px;
}

/* Иконка переключения узлов */
.tree-toggle {
    display: inline-block;
    width: 20px;
    text-align: center;
    cursor: pointer;
    margin-right: 5px;
    user-select: none;
    transition: all 0.2s ease;
}

.tree-toggle:hover {
    transform: scale(1.2);
    color: #007bff;
}

.tree-toggle:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

/* Скрытые элементы при сворачивании */
.tree-hidden {
    display: none !important;
}

/* Результаты поиска */
.hidden-by-search {
    display: none !important;
}
.highlight-search td {
    background-color: #fff3cd !important;
    animation: highlight-pulse 2s infinite alternate;
}
@keyframes highlight-pulse {
    0% { background-color: #fff3cd; }
    100% { background-color: #ffecb5; }
}

/* Стиль для иконок */
.tree-icon {
    margin-right: 5px;
    opacity: 0.8;
    transition: opacity 0.2s ease;
}
.tree-row:hover .tree-icon {
    opacity: 1;
}

/* Эффекты при наведении на строки */
tr.tree-row:hover td {
    background-color: #f5f5f5;
    transition: background-color 0.2s ease;
}

/* Стили для элементов дерева по типам */
.organization-row,
.subdivision-row,
.department-row {
    font-weight: 500;
    background-color: #f8f9fa;
    transition: background-color 0.3s ease;
}

/* Стиль для выбранной строки */
tr.selected-row td {
    background-color: #e8f4ff !important;
    animation: selected-row-pulse 2s infinite alternate;
}
@keyframes selected-row-pulse {
    0% { background-color: #e8f4ff; }
    100% { background-color: #d6eaff; }
}

/* Панель действий */
.actions-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 15px;
}

/* Кнопки действий */
.btn-group-sm .btn {
    transition: all 0.2s ease;
}

.btn-group-sm .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 5px rgba(0,0,0,0.15);
}

/* Счетчик выбранных элементов */
.select-count {
    margin-left: 10px;
    color: #666;
    font-size: 13px;
    transition: opacity 0.3s ease;
}

/* Результаты поиска */
.search-results {
    margin-top: 10px;
    padding: 5px 10px;
    border-radius: 4px;
    background-color: #f8f9fa;
    border-left: 3px solid #007bff;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
    .employee-checkbox {
        width: 24px;
        height: 24px;
    }

    .tree-toggle {
        width: 25px;
        height: 25px;
        line-height: 25px;
        font-size: 16px;
    }

    .actions-bar {
        flex-direction: column;
        align-items: flex-start;
    }

    .actions-bar .dropdown,
    .actions-bar .btn {
        width: 100%;
        margin-bottom: 5px;
    }
}
'''


def main():
    # Определение корневого пути проекта
    base_path = 'D:\\YandexDisk\\OT_online'

    # Проверка существования базовой директории
    if not os.path.exists(base_path):
        print(f"Ошибка: Директория {base_path} не существует.")
        print("Пожалуйста, укажите правильный путь к проекту.")
        sys.exit(1)

    # Создание директорий
    js_directory = os.path.join(base_path, 'static', 'directory', 'js')
    css_directory = os.path.join(base_path, 'static', 'directory', 'css')

    create_directory(js_directory)
    create_directory(css_directory)

    # Пути к файлам
    frontend_tree_view_js_path = os.path.join(js_directory, 'frontend_tree_view.js')
    frontend_tree_search_js_path = os.path.join(js_directory, 'frontend_tree_search.js')
    frontend_tree_view_css_path = os.path.join(css_directory, 'frontend_tree_view.css')

    # Создание файлов
    create_file(frontend_tree_view_js_path, frontend_tree_view_js)
    create_file(frontend_tree_search_js_path, frontend_tree_search_js)
    create_file(frontend_tree_view_css_path, frontend_tree_view_css)

    print("\nФайлы успешно созданы! Теперь подключите их в шаблоне employee_tree_view.html:")
    print('''
{% block extra_css %}
<link rel="stylesheet" href="{% static 'directory/css/frontend_tree_view.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'directory/js/frontend_tree_view.js' %}"></script>
<script src="{% static 'directory/js/frontend_tree_search.js' %}"></script>
{% endblock %}
''')


if __name__ == "__main__":
    main()