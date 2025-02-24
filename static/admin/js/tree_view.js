/**
 * 🌳 Ядро древовидного списка
 * Управляет деревом и подключаемыми модулями (сворачивание, разворачивание, чекбоксы)
 */
class TreeCore {
    constructor() {
        // 🎯 Основные элементы
        this.tree = document.getElementById('result_list');
        this.expandAllBtn = document.querySelector('.expand-all');
        this.collapseAllBtn = document.querySelector('.collapse-all');
        this.searchInput = document.querySelector('.tree-search');
        this.selectAllCheckbox = document.getElementById('select-all'); // Главный чекбокс "выбрать все"

        // Инициализация
        this.init();
    }

    init() {
        if (!this.tree) return;
        this._bindEvents();
        this._restoreState();
        this._initCheckboxes();
    }

    _bindEvents() {
        // Делегирование кликов в таблице
        this.tree.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-btn')) {
                this._handleToggleClick(e);
            }
        });

        if (this.expandAllBtn) {
            this.expandAllBtn.addEventListener('click', () => this.expandAll());
        }
        if (this.collapseAllBtn) {
            this.collapseAllBtn.addEventListener('click', () => this.collapseAll());
        }
    }

    _handleToggleClick(event) {
        const button = event.target;
        const row = button.closest('tr');
        const nodeId = row.dataset.nodeId;
        if (!nodeId) return;

        const isExpanded = button.getAttribute('data-state') === 'expanded';
        this.toggleNode(nodeId, !isExpanded);
    }

    toggleNode(nodeId, expand = true) {
        const row = this.tree.querySelector(`tr[data-node-id="${nodeId}"]`);
        if (!row) return;

        const button = row.querySelector('.toggle-btn');
        if (!button) return;

        button.setAttribute('data-state', expand ? 'expanded' : 'collapsed');
        button.textContent = expand ? '[-]' : '[+]';

        // Дочерние элементы
        const childRows = this.tree.querySelectorAll(`tr[data-parent-id="${nodeId}"]`);
        childRows.forEach(childRow => {
            childRow.classList.toggle('tree-row-hidden', !expand);
            if (!expand) {
                // Если сворачиваем родителя, сворачиваем и дочерние
                const childBtn = childRow.querySelector('.toggle-btn');
                if (childBtn) {
                    const cId = childRow.dataset.nodeId;
                    if (cId) {
                        this.toggleNode(cId, false);
                    }
                }
            }
        });

        this._saveState();
    }

    expandAll() {
        const buttons = this.tree.querySelectorAll('.toggle-btn[data-state="collapsed"]');
        buttons.forEach(btn => {
            const row = btn.closest('tr');
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                this.toggleNode(nodeId, true);
            }
        });
    }

    collapseAll() {
        // Сворачиваем только корневые, всё остальное автоматом сворачивается
        const rootRows = this.tree.querySelectorAll('tr[data-level="0"]');
        rootRows.forEach(row => {
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                this.toggleNode(nodeId, false);
            }
        });
    }

    _saveState() {
        const state = {};
        this.tree.querySelectorAll('.toggle-btn').forEach(btn => {
            const row = btn.closest('tr');
            const nodeId = row.dataset.nodeId;
            if (nodeId) {
                state[nodeId] = btn.getAttribute('data-state');
            }
        });
        localStorage.setItem('treeViewState', JSON.stringify(state));
    }

    _restoreState() {
        try {
            const state = JSON.parse(localStorage.getItem('treeViewState'));
            if (state) {
                Object.entries(state).forEach(([nodeId, st]) => {
                    this.toggleNode(nodeId, st === 'expanded');
                });
            }
        } catch (err) {
            console.error('Error restoring tree state:', err);
        }
    }

    _initCheckboxes() {
        if (!this.selectAllCheckbox) return;

        this.selectAllCheckbox.addEventListener('change', () => {
            const checkboxes = this.tree.querySelectorAll('input[name="_selected_action"]');
            checkboxes.forEach(ch => {
                ch.checked = this.selectAllCheckbox.checked;
            });
            this._updateSelectedCounter();
        });

        this.tree.addEventListener('change', (e) => {
            if (e.target.classList.contains('action-select')) {
                this._updateSelectAllState();
            }
        });
    }

    _updateSelectAllState() {
        if (!this.selectAllCheckbox) return;
        const checkboxes = this.tree.querySelectorAll('input[name="_selected_action"]');
        const checked = this.tree.querySelectorAll('input[name="_selected_action"]:checked');

        this.selectAllCheckbox.checked = (checkboxes.length === checked.length);
        this.selectAllCheckbox.indeterminate = (checked.length > 0 && checked.length < checkboxes.length);

        this._updateSelectedCounter();
    }

    _updateSelectedCounter() {
        const counter = document.querySelector('.action-counter');
        if (counter) {
            const total = this.tree.querySelectorAll('input[name="_selected_action"]').length;
            const selected = this.tree.querySelectorAll('input[name="_selected_action"]:checked').length;
            counter.textContent = `${selected} из ${total} выбрано`;
            counter.style.display = selected > 0 ? 'inline' : 'none';
        }
    }
}

// Автоинициализация
document.addEventListener('DOMContentLoaded', () => {
    window.treeCore = new TreeCore();
});
