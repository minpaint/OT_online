/**
 * 🌳 Ядро древовидного списка
 * Управляет деревом и подключаемыми модулями (сворачивание, разворачивание, чекбоксы)
 * Модифицировано: добавлен выбор только одного элемента
 */
class TreeCore {
    constructor() {
        // 🎯 Основные элементы
        this.tree = document.getElementById('employeeTree') || document.getElementById('result_list');
        this.expandAllBtn = document.querySelector('.expand-all') || document.querySelector('#btnExpandAll');
        this.collapseAllBtn = document.querySelector('.collapse-all') || document.querySelector('#btnCollapseAll');
        this.searchInput = document.querySelector('.tree-search') || document.querySelector('#localSearchInput');
        this.selectAllCheckbox = document.getElementById('select-all'); // Главный чекбокс "выбрать все"

        // 💾 Массив для хранения выбранных элементов (для режима одиночного выбора - только один элемент)
        this.selectedItems = [];

        // 🛠️ Настройки
        this.singleSelectMode = true; // Режим выбора только одного элемента

        // Инициализация
        if (this.tree) {
            this.init();
            console.log('✅ TreeCore инициализирован');
        } else {
            console.log('❌ Дерево не найдено на странице');
        }
    }

    /**
     * 🚀 Инициализация всех компонентов
     */
    init() {
        // Добавляем класс для стилизации режима одиночного выбора
        if (this.singleSelectMode && this.tree) {
            this.tree.classList.add('single-select-mode');
        }

        // Инициализация обработчиков событий
        this._bindEvents();

        // Восстановление состояния дерева
        this._restoreState();

        // Инициализация чекбоксов
        if (this.singleSelectMode) {
            this._initSingleSelectCheckboxes();
        } else {
            this._initCheckboxes();
        }

        // Инициализация кнопок действий
        this._initActionButtons();
    }

    /**
     * 🔄 Привязка основных обработчиков событий
     */
    _bindEvents() {
        // Делегирование кликов в таблице для переключателей
        if (this.tree) {
            this.tree.addEventListener('click', (e) => {
                // Обработка кликов по переключателям
                const toggle = e.target.closest('.tree-toggle');
                if (toggle) {
                    e.preventDefault(); // Предотвращаем действие по умолчанию
                    this._handleToggleClick(toggle);
                }
            });
        }

        // Обработчики для кнопок "Развернуть все" и "Свернуть все"
        if (this.expandAllBtn) {
            this.expandAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.expandAll();
            });
        }

        if (this.collapseAllBtn) {
            this.collapseAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.collapseAll();
            });
        }
    }

    /**
     * 🔄 Обработка клика по переключателю
     * @param {HTMLElement} toggle - Элемент переключателя
     */
    _handleToggleClick(toggle) {
        const nodeId = toggle.getAttribute('data-node');
        if (!nodeId) return;

        console.log(`🔄 Переключение узла: ${nodeId}`);

        // Определяем текущее состояние
        const isExpanded = toggle.textContent === '-';

        // Переключаем состояние
        this.toggleNode(nodeId, !isExpanded);
    }

    /**
     * 🔄 Переключение состояния узла (сворачивание/разворачивание)
     * @param {string} nodeId - ID узла
     * @param {boolean} expand - true для разворачивания, false для сворачивания
     */
    toggleNode(nodeId, expand = true) {
        if (!this.tree) return;

        const toggle = this.tree.querySelector(`.tree-toggle[data-node="${nodeId}"]`);
        if (!toggle) {
            console.log(`❌ Не найден переключатель для узла ${nodeId}`);
            return;
        }

        // Меняем текст переключателя
        toggle.textContent = expand ? '-' : '+';

        // Находим все дочерние элементы
        const children = this.tree.querySelectorAll(`[data-parent="${nodeId}"]`);

        if (children.length === 0) {
            console.log(`⚠️ Не найдено дочерних элементов для узла ${nodeId}`);
        }

        // Переключаем их видимость
        children.forEach(child => {
            if (expand) {
                child.classList.remove('tree-hidden');
            } else {
                child.classList.add('tree-hidden');
            }

            // Если сворачиваем родителя, сворачиваем и дочерние узлы
            if (!expand) {
                const childNodeId = child.getAttribute('data-node-id');
                if (childNodeId) {
                    const childToggle = child.querySelector('.tree-toggle');
                    if (childToggle && childToggle.textContent === '-') {
                        this.toggleNode(childNodeId, false);
                    }
                }
            }
        });

        // Сохраняем состояние в localStorage
        this._saveState();
    }

    /**
     * 🔄 Инициализация чекбоксов с выбором только одного элемента
     */
    _initSingleSelectCheckboxes() {
        if (!this.tree) return;

        // Очищаем массив выбранных элементов при инициализации
        this.selectedItems = [];

        // Делегирование событий для чекбоксов
        this.tree.addEventListener('change', (e) => {
            const checkbox = e.target;
            if (checkbox.type !== 'checkbox') return;

            // Получаем ID элемента
            const itemId = checkbox.getAttribute('data-id');
            if (!itemId) return;

            // Если чекбокс выбран, снимаем выделение с других чекбоксов
            if (checkbox.checked) {
                // Снимаем выделение со всех других чекбоксов
                this.tree.querySelectorAll('input[type="checkbox"]').forEach(otherCheckbox => {
                    if (otherCheckbox !== checkbox && otherCheckbox.checked) {
                        otherCheckbox.checked = false;
                    }
                });

                // Обновляем массив выбранных элементов
                this.selectedItems = [itemId];

                // Добавляем класс выделения для строки
                const row = checkbox.closest('tr');
                if (row) {
                    // Удаляем класс у всех строк
                    this.tree.querySelectorAll('tr.selected').forEach(r => {
                        r.classList.remove('selected');
                    });

                    // Добавляем класс выбранной строке
                    row.classList.add('selected');
                }
            } else {
                // Если чекбокс снят, удаляем ID из массива
                this.selectedItems = this.selectedItems.filter(id => id !== itemId);

                // Удаляем класс выделения для строки
                const row = checkbox.closest('tr');
                if (row) {
                    row.classList.remove('selected');
                }
            }

            // Обновляем счетчик выбранных элементов
            this._updateSelectedCounter();

            // Обновляем состояние кнопки действий
            this._updateActionsState();
        });

        console.log('📌 Инициализированы чекбоксы с режимом одиночного выбора');
    }

    /**
     * 🔄 Инициализация чекбоксов (стандартный режим)
     */
    _initCheckboxes() {
        if (!this.tree || !this.selectAllCheckbox) return;

        // Обработчик для главного чекбокса "Выбрать все"
        this.selectAllCheckbox.addEventListener('change', () => {
            const checkboxes = this.tree.querySelectorAll('input[type="checkbox"]:not(#select-all)');
            checkboxes.forEach(ch => {
                ch.checked = this.selectAllCheckbox.checked;

                // Обновляем массив выбранных элементов
                const itemId = ch.getAttribute('data-id');
                if (itemId) {
                    const index = this.selectedItems.indexOf(itemId);
                    if (ch.checked && index === -1) {
                        this.selectedItems.push(itemId);
                    } else if (!ch.checked && index !== -1) {
                        this.selectedItems.splice(index, 1);
                    }
                }
            });

            this._updateSelectedCounter();
        });

        // Делегирование событий для чекбоксов элементов
        this.tree.addEventListener('change', (e) => {
            const checkbox = e.target;
            if (checkbox.type !== 'checkbox' || checkbox === this.selectAllCheckbox) return;

            // Получаем ID элемента
            const itemId = checkbox.getAttribute('data-id');
            if (itemId) {
                const index = this.selectedItems.indexOf(itemId);
                if (checkbox.checked && index === -1) {
                    this.selectedItems.push(itemId);
                } else if (!checkbox.checked && index !== -1) {
                    this.selectedItems.splice(index, 1);
                }
            }

            this._updateSelectAllState();
            this._updateSelectedCounter();
        });
    }

    /**
     * 🔄 Обновление состояния главного чекбокса "Выбрать все"
     */
    _updateSelectAllState() {
        if (!this.tree || !this.selectAllCheckbox) return;

        const checkboxes = this.tree.querySelectorAll('input[type="checkbox"]:not(#select-all)');
        const checkedBoxes = this.tree.querySelectorAll('input[type="checkbox"]:checked:not(#select-all)');

        this.selectAllCheckbox.checked = checkboxes.length > 0 && checkboxes.length === checkedBoxes.length;
        this.selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < checkboxes.length;
    }

    /**
     * 🔄 Обновление счетчика выбранных элементов
     */
    _updateSelectedCounter() {
        const count = this.selectedItems.length;

        // Обновляем счетчик в блоке "Выбрано: X"
        const counterValue = document.getElementById('counterValue');
        if (counterValue) {
            counterValue.textContent = count;
        }

        // Обновляем видимость блока счетчика
        const selectedCounter = document.getElementById('selectedCounter');
        if (selectedCounter) {
            selectedCounter.style.display = count > 0 ? 'inline-block' : 'none';
        }

        // Обновляем счетчик в дропдауне
        const selectedCountBadge = document.getElementById('selectedCount');
        if (selectedCountBadge) {
            selectedCountBadge.textContent = count;
        }

        console.log(`🔄 Выбрано элементов: ${count}`);
    }

    /**
     * 🔄 Обновление состояния кнопок действий
     */
    _updateActionsState() {
        const count = this.selectedItems.length;

        // Обновляем состояние кнопки действий
        const actionsDropdown = document.getElementById('actionsDropdown');
        if (actionsDropdown) {
            actionsDropdown.disabled = count === 0;
        }
    }

    /**
     * 🔄 Инициализация кнопок действий
     */
    _initActionButtons() {
        // Кнопка "Карточка учета"
        const btnIssueCard = document.getElementById('btnIssueCard');
        if (btnIssueCard) {
            btnIssueCard.addEventListener('click', (e) => {
                e.preventDefault();
                if (this._validateSingleSelection()) {
                    const employeeId = this.selectedItems[0];
                    const urlElement = document.querySelector('[data-siz-personal-card-url]');
                    if (urlElement) {
                        const url = urlElement.getAttribute('data-siz-personal-card-url');
                        window.location.href = url.replace('0', employeeId);
                    }
                }
            });
        }

        // Кнопка "Выдать СИЗ"
        const btnIssueSIZ = document.getElementById('btnIssueSIZ');
        if (btnIssueSIZ) {
            btnIssueSIZ.addEventListener('click', (e) => {
                e.preventDefault();
                if (this._validateSingleSelection()) {
                    const employeeId = this.selectedItems[0];
                    const urlElement = document.querySelector('[data-siz-issue-url]');
                    if (urlElement) {
                        const url = urlElement.getAttribute('data-siz-issue-url');
                        window.location.href = url.replace('0', employeeId);
                    }
                }
            });
        }

        // Кнопка "Редактировать"
        const btnEditEmployee = document.getElementById('btnEditEmployee');
        if (btnEditEmployee) {
            btnEditEmployee.addEventListener('click', (e) => {
                e.preventDefault();
                if (this._validateSingleSelection()) {
                    const employeeId = this.selectedItems[0];
                    const urlElement = document.querySelector('[data-employee-update-url]');
                    if (urlElement) {
                        const url = urlElement.getAttribute('data-employee-update-url');
                        window.location.href = url.replace('0', employeeId);
                    }
                }
            });
        }
    }

    /**
     * 🔄 Проверка, что выбран один элемент
     * @returns {boolean} true, если выбран один элемент
     */
    _validateSingleSelection() {
        if (this.selectedItems.length === 0) {
            alert('Пожалуйста, выберите сотрудника.');
            return false;
        }

        return true;
    }

    /**
     * 🔄 Развернуть все узлы
     */
    expandAll() {
        if (!this.tree) return;

        console.log('🔄 Разворачиваем все узлы');

        // Находим все свернутые переключатели и разворачиваем их
        const collapsedToggles = this.tree.querySelectorAll('.tree-toggle');
        collapsedToggles.forEach(toggle => {
            if (toggle.textContent === '+') {
                const nodeId = toggle.getAttribute('data-node');
                if (nodeId) {
                    this.toggleNode(nodeId, true);
                }
            }
        });
    }

    /**
     * 🔄 Свернуть все узлы
     */
    collapseAll() {
        if (!this.tree) return;

        console.log('🔄 Сворачиваем все узлы');

        // Находим переключатели верхнего уровня (организации) и сворачиваем их
        const orgToggles = this.tree.querySelectorAll('.tree-toggle[data-node^="org-"]');

        if (orgToggles.length === 0) {
            // Если не нашли переключатели организаций, ищем любые развернутые переключатели
            const expandedToggles = this.tree.querySelectorAll('.tree-toggle');
            expandedToggles.forEach(toggle => {
                if (toggle.textContent === '-') {
                    const nodeId = toggle.getAttribute('data-node');
                    if (nodeId) {
                        this.toggleNode(nodeId, false);
                    }
                }
            });
        } else {
            // Сворачиваем переключатели организаций
            orgToggles.forEach(toggle => {
                if (toggle.textContent === '-') {
                    const nodeId = toggle.getAttribute('data-node');
                    if (nodeId) {
                        this.toggleNode(nodeId, false);
                    }
                }
            });
        }
    }

    /**
     * 🔄 Сохранение состояния дерева в localStorage
     */
    _saveState() {
        try {
            if (!this.tree) return;

            const state = {};

            this.tree.querySelectorAll('.tree-toggle').forEach(toggle => {
                const nodeId = toggle.getAttribute('data-node');
                if (nodeId) {
                    state[nodeId] = toggle.textContent === '-';
                }
            });

            localStorage.setItem('treeViewState', JSON.stringify(state));
        } catch (err) {
            console.error('Ошибка при сохранении состояния дерева:', err);
        }
    }

    /**
     * 🔄 Восстановление состояния дерева из localStorage
     */
    _restoreState() {
        try {
            if (!this.tree) return;

            const stateJson = localStorage.getItem('treeViewState');
            if (!stateJson) return;

            const state = JSON.parse(stateJson);

            // Восстанавливаем состояние каждого узла
            Object.entries(state).forEach(([nodeId, isExpanded]) => {
                this.toggleNode(nodeId, isExpanded);
            });
        } catch (err) {
            console.error('Ошибка при восстановлении состояния дерева:', err);
        }
    }

    /**
     * 🔄 Получение выбранных элементов
     * @returns {Array} Массив ID выбранных элементов
     */
    getSelectedItems() {
        return [...this.selectedItems];
    }
}

// Переопределяем функцию initEmployeeTree из main.js
window.initEmployeeTree = function() {
    console.log('🔄 Функция initEmployeeTree переопределена');
    // Инициализируем наш класс
    if (!window.treeCore) {
        window.treeCore = new TreeCore();
    }
};

// Автоинициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔄 DOM загружен, проверяем инициализацию TreeCore');

    // Проверяем, был ли уже создан treeCore
    if (!window.treeCore) {
        console.log('🔄 Инициализируем TreeCore');
        window.treeCore = new TreeCore();
    }
});