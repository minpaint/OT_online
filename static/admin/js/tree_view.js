/**
 * 🌳 Ядро древовидного списка
 * Управляет деревом и подключаемыми модулями
 */
class TreeCore {
    constructor() {
        // 🎯 Основные элементы
        this.tree = document.getElementById('result_list');
        this.expandAllBtn = document.querySelector('.expand-all');
        this.collapseAllBtn = document.querySelector('.collapse-all');
        this.searchInput = document.querySelector('.tree-search');

        // 🔌 Подключаемые модули
        this.plugins = new Map();

        // Инициализация
        this.init();
    }

    /**
     * 🚀 Инициализация дерева
     */
    init() {
        if (!this.tree) return;

        // Привязываем обработчики событий
        this._bindEvents();

        // Восстанавливаем состояние
        this._restoreState();
    }

    /**
     * 📌 Привязка обработчиков событий
     */
    _bindEvents() {
        // Делегирование кликов на дереве
        this.tree.addEventListener('click', (e) => {
            // Клик по кнопке разворачивания
            if (e.target.classList.contains('toggle-btn')) {
                this._handleToggleClick(e);
            }
        });

        // Кнопки управления
        if (this.expandAllBtn) {
            this.expandAllBtn.addEventListener('click', () => this.expandAll());
        }
        if (this.collapseAllBtn) {
            this.collapseAllBtn.addEventListener('click', () => this.collapseAll());
        }
    }

    /**
     * 🔄 Обработка клика по кнопке разворачивания
     */
    _handleToggleClick(event) {
        const button = event.target;
        const row = button.closest('tr');
        const nodeId = row.dataset.nodeId;

        if (!nodeId) return;

        const isExpanded = button.getAttribute('data-state') === 'expanded';
        this.toggleNode(nodeId, !isExpanded);
    }

    /**
     * 📖 Развернуть/свернуть узел
     */
    toggleNode(nodeId, expand = true) {
        const row = this.tree.querySelector(`tr[data-node-id="${nodeId}"]`);
        if (!row) return;

        const button = row.querySelector('.toggle-btn');
        if (!button) return;

        // Обновляем состояние кнопки
        button.setAttribute('data-state', expand ? 'expanded' : 'collapsed');
        button.textContent = expand ? '[-]' : '[+]';

        // Обновляем видимость дочерних элементов
        const childRows = this.tree.querySelectorAll(`tr[data-parent-id="${nodeId}"]`);
        childRows.forEach(childRow => {
            childRow.classList.toggle('tree-row-hidden', !expand);

            // Если сворачиваем родителя, сворачиваем и дочерние узлы
            if (!expand) {
                const childButton = childRow.querySelector('.toggle-btn');
                if (childButton) {
                    const childId = childRow.dataset.nodeId;
                    if (childId) {
                        this.toggleNode(childId, false);
                    }
                }
            }
        });

        // Сохраняем состояние
        this._saveState();
    }

    /**
     * ⬇️ Развернуть все узлы
     */
    expandAll() {
        const buttons = this.tree.querySelectorAll('.toggle-btn[data-state="collapsed"]');
        buttons.forEach(button => {
            const row = button.closest('tr');
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                this.toggleNode(nodeId, true);
            }
        });
    }

    /**
     * ⬆️ Свернуть все узлы
     */
    collapseAll() {
        // Собираем все корневые узлы (с data-level="0")
        const rootRows = this.tree.querySelectorAll('tr[data-level="0"]');
        rootRows.forEach(row => {
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                this.toggleNode(nodeId, false);
            }
        });
    }

    /**
     * 💾 Сохранение состояния дерева
     */
    _saveState() {
        const state = {};
        this.tree.querySelectorAll('.toggle-btn').forEach(button => {
            const row = button.closest('tr');
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                state[nodeId] = button.getAttribute('data-state');
            }
        });
        localStorage.setItem('treeViewState', JSON.stringify(state));
    }

    /**
     * 🔄 Восстановление состояния дерева
     */
    _restoreState() {
        try {
            const state = JSON.parse(localStorage.getItem('treeViewState'));
            if (state) {
                Object.entries(state).forEach(([nodeId, isExpanded]) => {
                    this.toggleNode(nodeId, isExpanded === 'expanded');
                });
            }
        } catch (e) {
            console.error('Error restoring tree state:', e);
        }
    }

    /**
     * 🔌 Регистрация плагина
     */
    registerPlugin(name, plugin) {
        if (this.plugins.has(name)) {
            console.warn(`Plugin ${name} is already registered`);
            return;
        }
        this.plugins.set(name, new plugin(this));
    }
}

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.treeCore = new TreeCore();
});