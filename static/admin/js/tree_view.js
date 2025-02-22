document.addEventListener('DOMContentLoaded', function() {
    class TreeView {
        constructor() {
            // Инициализация основных элементов
            this.treeTable = document.getElementById('result_list');
            if (!this.treeTable) return;

            // Поиск элементов управления
            this.expandAllBtn = document.querySelector('.expand-all');
            this.collapseAllBtn = document.querySelector('.collapse-all');

            // Инициализация поиска
            this.search = new TreeSearch(this.treeTable);

            // Привязка обработчиков событий
            this.bindEvents();

            // Восстановление состояния дерева
            this.restoreTreeState();
        }

        bindEvents() {
            // Обработчик кликов по кнопкам сворачивания/разворачивания
            this.treeTable.addEventListener('click', (e) => {
                if (e.target.classList.contains('toggle-btn')) {
                    const row = e.target.closest('tr');
                    const nodeId = row.getAttribute('data-node-id');
                    if (nodeId) {
                        this.toggleNode(e.target, nodeId);
                    }
                }
            });

            // Обработчики для кнопок "Развернуть/Свернуть все"
            if (this.expandAllBtn) {
                this.expandAllBtn.addEventListener('click', () => this.expandAll());
            }
            if (this.collapseAllBtn) {
                this.collapseAllBtn.addEventListener('click', () => this.collapseAll());
            }
        }

        toggleNode(button, nodeId) {
            const childRows = this.getChildRows(nodeId);
            const isExpanded = button.getAttribute('data-state') === 'expanded';

            // Обновляем состояние кнопки
            button.setAttribute('data-state', isExpanded ? 'collapsed' : 'expanded');
            button.textContent = isExpanded ? '[+]' : '[-]';

            // Обновляем видимость дочерних элементов
            childRows.forEach(row => {
                row.classList.toggle('tree-row-hidden', isExpanded);

                // Если сворачиваем узел, сворачиваем все дочерние узлы
                if (isExpanded) {
                    const childButton = row.querySelector('.toggle-btn');
                    if (childButton) {
                        childButton.setAttribute('data-state', 'collapsed');
                        childButton.textContent = '[+]';
                        const childId = row.getAttribute('data-node-id');
                        if (childId) {
                            this.getChildRows(childId).forEach(childRow => {
                                childRow.classList.add('tree-row-hidden');
                            });
                        }
                    }
                }
            });

            // Сохраняем состояние
            this.saveTreeState();
        }

        getChildRows(parentId) {
            return Array.from(this.treeTable.querySelectorAll(`tr[data-parent-id="${parentId}"]`));
        }

        expandAll() {
            const buttons = this.treeTable.querySelectorAll('.toggle-btn[data-state="collapsed"]');
            buttons.forEach(button => {
                const row = button.closest('tr');
                const nodeId = row.getAttribute('data-node-id');
                if (nodeId) {
                    this.toggleNode(button, nodeId);
                }
            });
        }

        collapseAll() {
            const buttons = this.treeTable.querySelectorAll('.toggle-btn[data-state="expanded"]');
            Array.from(buttons).reverse().forEach(button => {
                const row = button.closest('tr');
                const nodeId = row.getAttribute('data-node-id');
                if (nodeId) {
                    this.toggleNode(button, nodeId);
                }
            });
        }

        updateToggleButtons() {
            const rows = this.treeTable.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const button = row.querySelector('.toggle-btn');
                const nodeId = row.getAttribute('data-node-id');
                if (button && nodeId) {
                    const hasVisibleChild = this.getChildRows(nodeId).some(
                        child => !child.classList.contains('tree-row-hidden')
                    );
                    button.style.display = hasVisibleChild ? '' : 'none';
                }
            });
        }

        saveTreeState() {
            const state = {};
            this.treeTable.querySelectorAll('.toggle-btn').forEach(button => {
                const row = button.closest('tr');
                const nodeId = row.getAttribute('data-node-id');
                if (nodeId) {
                    state[nodeId] = button.getAttribute('data-state');
                }
            });
            localStorage.setItem('treeViewState', JSON.stringify(state));
        }

        restoreTreeState() {
            try {
                const state = JSON.parse(localStorage.getItem('treeViewState'));
                if (state) {
                    this.treeTable.querySelectorAll('.toggle-btn').forEach(button => {
                        const row = button.closest('tr');
                        const nodeId = row.getAttribute('data-node-id');
                        if (nodeId && state[nodeId]) {
                            if (state[nodeId] !== button.getAttribute('data-state')) {
                                this.toggleNode(button, nodeId);
                            }
                        }
                    });
                }
            } catch (e) {
                console.error('Error restoring tree state:', e);
            }
        }
    }

    // Инициализация при загрузке страницы
    new TreeView();
});