/**
 * 🌳 Ядро древовидного списка
 * Управляет деревом и подключаемыми модулями (сворачивание, разворачивание, чекбоксы)
 */
class TreeCore {
    constructor() {
        // 🎯 Основные элементы
        this.tree = document.getElementById('result_list') || document.getElementById('employeeTree');
        this.expandAllBtn = document.querySelector('.expand-all');
        this.collapseAllBtn = document.querySelector('.collapse-all');
        this.searchInput = document.querySelector('.tree-search') || document.getElementById('localSearchInput');
        this.selectAllCheckbox = document.getElementById('select-all'); // Главный чекбокс "выбрать все"

        // Элементы для работы с выбранными сотрудниками
        this.actionsDropdown = document.getElementById('actionsDropdown');
        this.selectedCounter = document.getElementById('selectedCounter');
        this.counterValue = document.getElementById('counterValue');

        this.selectedEmployees = []; // Массив выбранных сотрудников

        // Определяем режим работы (админка или фронтенд)
        this.isAdminMode = this.tree && this.tree.id === 'result_list';

        // Инициализация
        this.init();
    }

    init() {
        if (!this.tree) return;
        this._bindEvents();
        this._restoreState();
        this._initCheckboxes();

        // Инициализация действий с сотрудниками, если нужно
        this._initEmployeeActions();
    }

    _bindEvents() {
        // Делегирование кликов в таблице
        this.tree.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-btn') || e.target.classList.contains('tree-toggle')) {
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
        const button = event.target.closest('.toggle-btn, .tree-toggle');
        if (!button) return;

        let row, nodeId;

        if (button.classList.contains('toggle-btn')) {
            row = button.closest('tr');
            nodeId = row.dataset.nodeId;
            const isExpanded = button.getAttribute('data-state') === 'expanded';
            this.toggleNode(nodeId, !isExpanded);
        } else if (button.classList.contains('tree-toggle')) {
            nodeId = button.dataset.node;
            const isExpanded = button.textContent === '-';
            this.toggleNodeByToggleIcon(nodeId, !isExpanded);
        }
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
    }

    expandAll() {
        // Проверяем тип toggle-элементов
        const hasToggleBtn = this.tree.querySelector('.toggle-btn');
        const hasTreeToggle = this.tree.querySelector('.tree-toggle');

        if (hasToggleBtn) {
            const buttons = this.tree.querySelectorAll('.toggle-btn[data-state="collapsed"]');
            buttons.forEach(btn => {
                const row = btn.closest('tr');
                const nodeId = row.dataset.nodeId;
                if (nodeId) {
                    this.toggleNode(nodeId, true);
                }
            });
        } else if (hasTreeToggle) {
            const toggles = this.tree.querySelectorAll('.tree-toggle');
            toggles.forEach(toggle => {
                const nodeId = toggle.dataset.node;
                if (nodeId) {
                    this.toggleNodeByToggleIcon(nodeId, true);
                }
            });
        }
    }

    collapseAll() {
        // Проверяем тип toggle-элементов
        const hasToggleBtn = this.tree.querySelector('.toggle-btn');
        const hasTreeToggle = this.tree.querySelector('.tree-toggle');

        if (hasToggleBtn) {
            // Сворачиваем только корневые, всё остальное автоматом сворачивается
            const rootRows = this.tree.querySelectorAll('tr[data-level="0"]');
            rootRows.forEach(row => {
                const nodeId = row.dataset.nodeId;
                if (nodeId) {
                    this.toggleNode(nodeId, false);
                }
            });
        } else if (hasTreeToggle) {
            // Сворачиваем только корневые элементы (организации)
            const orgNodes = this.tree.querySelectorAll('.tree-toggle[data-node^="org-"]');
            orgNodes.forEach(node => {
                const nodeId = node.dataset.node;
                this.toggleNodeByToggleIcon(nodeId, false);
            });
        }
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
            const checkboxes = this.tree.querySelectorAll('input[name="_selected_action"], .employee-checkbox');
            checkboxes.forEach(ch => {
                ch.checked = this.selectAllCheckbox.checked;

                // Если это чекбокс сотрудника, обрабатываем его
                if (ch.classList.contains('employee-checkbox')) {
                    const employeeId = ch.dataset.id;
                    const index = this.selectedEmployees.indexOf(employeeId);

                    if (this.selectAllCheckbox.checked && index === -1) {
                        this.selectedEmployees.push(employeeId);
                    } else if (!this.selectAllCheckbox.checked && index !== -1) {
                        this.selectedEmployees.splice(index, 1);
                    }
                }
            });

            this._updateSelectedCounter();
        });

        this.tree.addEventListener('change', (e) => {
            const checkbox = e.target;
            if (!checkbox.matches('input[type="checkbox"]')) return;

            if (checkbox.classList.contains('employee-checkbox')) {
                // Обработка выбора сотрудника
                const employeeId = checkbox.dataset.id;
                const index = this.selectedEmployees.indexOf(employeeId);

                if (checkbox.checked && index === -1) {
                    this.selectedEmployees.push(employeeId);
                } else if (!checkbox.checked && index !== -1) {
                    this.selectedEmployees.splice(index, 1);
                }

                this._updateSelectedCounter();
            } else if (checkbox.classList.contains('org-checkbox') ||
                      checkbox.classList.contains('sub-checkbox') ||
                      checkbox.classList.contains('dept-checkbox')) {
                // Обработка выбора группы (организация/подразделение/отдел)
                const nodeId = checkbox.dataset.id;
                const children = this.tree.querySelectorAll(`tr[data-parent="${nodeId}"] input[type="checkbox"]`);

                children.forEach(childCheckbox => {
                    childCheckbox.checked = checkbox.checked;

                    // Если это сотрудник, обновляем массив выбранных
                    if (childCheckbox.classList.contains('employee-checkbox')) {
                        const empId = childCheckbox.dataset.id;
                        const index = this.selectedEmployees.indexOf(empId);

                        if (checkbox.checked && index === -1) {
                            this.selectedEmployees.push(empId);
                        } else if (!checkbox.checked && index !== -1) {
                            this.selectedEmployees.splice(index, 1);
                        }
                    }
                });

                this._updateSelectedCounter();
            } else if (checkbox.classList.contains('action-select')) {
                this._updateSelectAllState();
            }
        });
    }

    _updateSelectAllState() {
        if (!this.selectAllCheckbox) return;
        const checkboxes = this.tree.querySelectorAll('input[name="_selected_action"], .employee-checkbox');
        const checked = this.tree.querySelectorAll('input[name="_selected_action"]:checked, .employee-checkbox:checked');

        this.selectAllCheckbox.checked = (checkboxes.length === checked.length);
        this.selectAllCheckbox.indeterminate = (checked.length > 0 && checked.length < checkboxes.length);

        this._updateSelectedCounter();
    }

    _updateSelectedCounter() {
        // Обновляем счетчик выбранных элементов
        const count = this.selectedEmployees.length;

        if (this.counterValue) {
            this.counterValue.textContent = count;
        }

        if (this.selectedCounter) {
            if (count > 0) {
                this.selectedCounter.style.display = 'inline-block';
            } else {
                this.selectedCounter.style.display = 'none';
            }
        }

        if (this.actionsDropdown) {
            this.actionsDropdown.disabled = count === 0;
        }

        // Обновляем счетчик в дропдауне, если он есть
        const selectedCountBadge = document.getElementById('selectedCount');
        if (selectedCountBadge) {
            selectedCountBadge.textContent = count;
        }

        // Также обновляем счетчик в форме админки, если он есть
        const actionCounter = document.querySelector('.action-counter');
        if (actionCounter) {
            const total = this.tree.querySelectorAll('input[name="_selected_action"]').length;
            const selected = this.tree.querySelectorAll('input[name="_selected_action"]:checked').length;
            actionCounter.textContent = `${selected} из ${total} выбрано`;
            actionCounter.style.display = selected > 0 ? 'inline' : 'none';
        }
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
                if (this.selectedEmployees.length === 0) {
                    alert('Пожалуйста, выберите сотрудника для просмотра карточки учета.');
                    return;
                }

                if (this.selectedEmployees.length > 1) {
                    alert('Пожалуйста, выберите только одного сотрудника для просмотра карточки учета.');
                    return;
                }

                // Переходим на страницу карточки учета выбранного сотрудника
                const employeeId = this.selectedEmployees[0];
                const url = document.querySelector('[data-siz-personal-card-url]')?.dataset.sizPersonalCardUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }

        if (btnIssueSIZ) {
            btnIssueSIZ.addEventListener('click', () => {
                if (this.selectedEmployees.length === 0) {
                    alert('Пожалуйста, выберите сотрудника для выдачи СИЗ.');
                    return;
                }

                if (this.selectedEmployees.length > 1) {
                    alert('Пожалуйста, выберите только одного сотрудника для выдачи СИЗ.');
                    return;
                }

                // Формируем URL с параметром выбранного сотрудника
                const employeeId = this.selectedEmployees[0];
                const url = document.querySelector('[data-siz-issue-url]')?.dataset.sizIssueUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }

        if (btnEditEmployee) {
            btnEditEmployee.addEventListener('click', () => {
                if (this.selectedEmployees.length === 0) {
                    alert('Пожалуйста, выберите сотрудника для редактирования.');
                    return;
                }

                if (this.selectedEmployees.length > 1) {
                    alert('Пожалуйста, выберите только одного сотрудника для редактирования.');
                    return;
                }

                // Переходим на страницу редактирования выбранного сотрудника
                const employeeId = this.selectedEmployees[0];
                const url = document.querySelector('[data-employee-update-url]')?.dataset.employeeUpdateUrl || '';
                window.location.href = url.replace('0', employeeId);
            });
        }
    }
}

// Автоинициализация
document.addEventListener('DOMContentLoaded', () => {
    window.treeCore = new TreeCore();
});