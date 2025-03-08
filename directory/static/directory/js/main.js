// Функция для обновления списка подразделений
function updateSubdivisions(organizationId, targetSelect) {
    if (!organizationId) {
        $(targetSelect).html('<option value="">---------</option>');
        return;
    }

    $.ajax({
        url: '/api/subdivisions/',
        data: { organization: organizationId },
        success: function(data) {
            let options = '<option value="">---------</option>';
            data.forEach(item => {
                options += `<option value="${item.id}">${item.name}</option>`;
            });
            $(targetSelect).html(options);
        }
    });
}

// Функция для обновления списка должностей
function updatePositions(subdivisionId, targetSelect) {
    if (!subdivisionId) {
        $(targetSelect).html('<option value="">---------</option>');
        return;
    }

    $.ajax({
        url: '/api/positions/',
        data: { subdivision: subdivisionId },
        success: function(data) {
            let options = '<option value="">---------</option>';
            data.forEach(item => {
                options += `<option value="${item.id}">${item.name}</option>`;
            });
            $(targetSelect).html(options);
        }
    });
}

// Инициализация всплывающих подсказок Bootstrap
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

// Автоматическое скрытие сообщений об успехе
$(document).ready(function() {
    setTimeout(function() {
        $('.alert-success').fadeOut('slow');
    }, 3000);

    // Инициализация функций для работы с деревом сотрудников
    initEmployeeTree();
});

// Подтверждение удаления
function confirmDelete(event, message) {
    if (!confirm(message || 'Вы уверены, что хотите удалить этот элемент?')) {
        event.preventDefault();
    }
}

/**
 * 🌳 Инициализация дерева сотрудников
 */
function initEmployeeTree() {
    // Проверяем, есть ли дерево на странице
    const employeeTree = document.getElementById('employeeTree');
    if (!employeeTree) return;

    // Переменные для работы с выбранными сотрудниками
    let selectedEmployees = [];

    // Функция для обновления счетчика выбранных сотрудников
    function updateSelectedCounter() {
        const count = selectedEmployees.length;
        const counterValue = document.getElementById('counterValue');
        const selectedCounter = document.getElementById('selectedCounter');
        const actionsDropdown = document.getElementById('actionsDropdown');

        if (counterValue) counterValue.textContent = count;

        if (selectedCounter) {
            selectedCounter.style.display = count > 0 ? 'inline-block' : 'none';
        }

        if (actionsDropdown) {
            actionsDropdown.disabled = count === 0;
        }

        // Обновляем счетчик в дропдауне
        const selectedCountBadge = document.getElementById('selectedCount');
        if (selectedCountBadge) {
            selectedCountBadge.textContent = count;
        }
    }

    // Обработка выбора всех чекбоксов
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const employeeCheckboxes = employeeTree.querySelectorAll('.employee-checkbox');

            employeeCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;

                const employeeId = checkbox.dataset.id;
                const index = selectedEmployees.indexOf(employeeId);

                if (selectAllCheckbox.checked && index === -1) {
                    selectedEmployees.push(employeeId);
                } else if (!selectAllCheckbox.checked && index !== -1) {
                    selectedEmployees.splice(index, 1);
                }
            });

            updateSelectedCounter();
        });
    }

    // Обработка выбора отдельных чекбоксов
    employeeTree.addEventListener('change', function(e) {
        const checkbox = e.target;
        if (!checkbox.matches('input[type="checkbox"]')) return;

        if (checkbox.classList.contains('employee-checkbox')) {
            // Обработка выбора сотрудника
            const employeeId = checkbox.dataset.id;
            const index = selectedEmployees.indexOf(employeeId);

            if (checkbox.checked && index === -1) {
                selectedEmployees.push(employeeId);
            } else if (!checkbox.checked && index !== -1) {
                selectedEmployees.splice(index, 1);
            }

            updateSelectedCounter();
        } else if (checkbox.classList.contains('org-checkbox') ||
                  checkbox.classList.contains('sub-checkbox') ||
                  checkbox.classList.contains('dept-checkbox')) {
            // Обработка выбора группы (организация/подразделение/отдел)
            const nodeId = checkbox.dataset.id;
            const children = employeeTree.querySelectorAll(`tr[data-parent="${nodeId}"] input[type="checkbox"]`);

            children.forEach(childCheckbox => {
                childCheckbox.checked = checkbox.checked;

                // Если это сотрудник, обновляем массив выбранных
                if (childCheckbox.classList.contains('employee-checkbox')) {
                    const empId = childCheckbox.dataset.id;
                    const index = selectedEmployees.indexOf(empId);

                    if (checkbox.checked && index === -1) {
                        selectedEmployees.push(empId);
                    } else if (!checkbox.checked && index !== -1) {
                        selectedEmployees.splice(index, 1);
                    }
                }
            });

            updateSelectedCounter();
        }

        // Проверяем, выбраны ли все сотрудники
        const allEmployeeCheckboxes = employeeTree.querySelectorAll('.employee-checkbox');
        const checkedEmployeeCheckboxes = employeeTree.querySelectorAll('.employee-checkbox:checked');

        if (selectAllCheckbox) {
            selectAllCheckbox.checked =
                allEmployeeCheckboxes.length > 0 &&
                allEmployeeCheckboxes.length === checkedEmployeeCheckboxes.length;

            // Определяем, выбраны ли частично (indeterminate)
            selectAllCheckbox.indeterminate =
                checkedEmployeeCheckboxes.length > 0 &&
                checkedEmployeeCheckboxes.length < allEmployeeCheckboxes.length;
        }
    });

    // 🌳 Функция для переключения узла дерева
    function toggleNode(nodeId, expand = true) {
        const toggleElement = employeeTree.querySelector(`.tree-toggle[data-node="${nodeId}"]`);
        if (!toggleElement) return;

        toggleElement.textContent = expand ? '-' : '+';

        const children = employeeTree.querySelectorAll(`tr[data-parent="${nodeId}"]`);
        children.forEach(child => {
            if (expand) {
                child.classList.remove('tree-hidden');
            } else {
                child.classList.add('tree-hidden');

                // Проверяем, есть ли у ребенка свои дети
                const childNodeId = child.dataset.nodeId;
                if (childNodeId) {
                    toggleNode(childNodeId, false);
                }
            }
        });
    }

    // Обработка кликов по иконкам сворачивания/разворачивания
    employeeTree.addEventListener('click', function(e) {
        const toggleElement = e.target.closest('.tree-toggle');
        if (!toggleElement) return;

        const nodeId = toggleElement.dataset.node;
        const isExpanded = toggleElement.textContent === '-';
        toggleNode(nodeId, !isExpanded);
    });

    // Обработка кнопки "Развернуть все"
    const btnExpandAll = document.getElementById('btnExpandAll');
    if (btnExpandAll) {
        btnExpandAll.addEventListener('click', function() {
            const nodes = employeeTree.querySelectorAll('.tree-toggle');
            nodes.forEach(node => {
                const nodeId = node.dataset.node;
                toggleNode(nodeId, true);
            });
        });
    }

    // Обработка кнопки "Свернуть все"
    const btnCollapseAll = document.getElementById('btnCollapseAll');
    if (btnCollapseAll) {
        btnCollapseAll.addEventListener('click', function() {
            const orgNodes = employeeTree.querySelectorAll('.tree-toggle[data-node^="org-"]');
            orgNodes.forEach(node => {
                const nodeId = node.dataset.node;
                toggleNode(nodeId, false);
            });
        });
    }

    // 📝 Обработка кнопки "Принять на работу"
    const btnHireEmployee = document.getElementById('btnHireEmployee');
    if (btnHireEmployee) {
        btnHireEmployee.addEventListener('click', function() {
            // Перенаправляем на страницу найма
            const hireUrl = btnHireEmployee.dataset.hireUrl || '/directory/employees/hire/';
            window.location.href = hireUrl;
        });
    }

    // 🛡️ Обработка кнопки "Выдать СИЗ"
    const btnIssueSIZ = document.getElementById('btnIssueSIZ');
    if (btnIssueSIZ) {
        btnIssueSIZ.addEventListener('click', function() {
            if (selectedEmployees.length === 0) {
                alert('Пожалуйста, выберите сотрудника для выдачи СИЗ.');
                return;
            }

            if (selectedEmployees.length > 1) {
                alert('Пожалуйста, выберите только одного сотрудника для выдачи СИЗ.');
                return;
            }

            // Формируем URL с параметром выбранного сотрудника
            const employeeId = selectedEmployees[0];
            const issueUrl = btnIssueSIZ.dataset.issueUrl || `/directory/siz/issue/employee/${employeeId}/`;

            // Перенаправляем на страницу выдачи СИЗ
            window.location.href = issueUrl;
        });
    }

    // 📋 Обработка кнопки "Карточка учета"
    const btnIssueCard = document.getElementById('btnIssueCard');
    if (btnIssueCard) {
        btnIssueCard.addEventListener('click', function() {
            if (selectedEmployees.length === 0) {
                alert('Пожалуйста, выберите сотрудника для просмотра карточки учета.');
                return;
            }

            if (selectedEmployees.length > 1) {
                alert('Пожалуйста, выберите только одного сотрудника для просмотра карточки учета.');
                return;
            }

            // Переходим на страницу карточки учета выбранного сотрудника
            const employeeId = selectedEmployees[0];
            const cardUrl = btnIssueCard.dataset.cardUrl || `/directory/siz/personal-card/${employeeId}/`;
            window.location.href = cardUrl;
        });
    }

    // ✏️ Обработка кнопки "Редактировать"
    const btnEditEmployee = document.getElementById('btnEditEmployee');
    if (btnEditEmployee) {
        btnEditEmployee.addEventListener('click', function() {
            if (selectedEmployees.length === 0) {
                alert('Пожалуйста, выберите сотрудника для редактирования.');
                return;
            }

            if (selectedEmployees.length > 1) {
                alert('Пожалуйста, выберите только одного сотрудника для редактирования.');
                return;
            }

            // Переходим на страницу редактирования выбранного сотрудника
            const employeeId = selectedEmployees[0];
            const editUrl = btnEditEmployee.dataset.editUrl || `/directory/employees/${employeeId}/update/`;
            window.location.href = editUrl;
        });
    }

    // 🔍 Инициализация поиска по дереву
    const localSearchInput = document.getElementById('localSearchInput');
    const localSearchBtn = document.getElementById('localSearchBtn');
    const clearSearchBtn = document.getElementById('clearSearchBtn');

    if (localSearchInput) {
        // Инициализируем поисковый механизм
        const treeSearch = new TreeSearch(employeeTree);

        // Обработка ввода в поле поиска
        localSearchInput.addEventListener('input', function(e) {
            treeSearch.search(e.target.value);
        });

        // Обработка нажатия Enter в поле поиска
        localSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                treeSearch.search(e.target.value);
            } else if (e.key === 'Escape') {
                localSearchInput.value = '';
                treeSearch.search('');
            }
        });

        // Обработка кнопки поиска
        if (localSearchBtn) {
            localSearchBtn.addEventListener('click', function() {
                treeSearch.search(localSearchInput.value);
            });
        }

        // Обработка кнопки очистки
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', function() {
                localSearchInput.value = '';
                treeSearch.search('');
            });
        }
    }

    // 🔍 Инициализация - сначала разворачиваем только организации
    const subAndDeptNodes = employeeTree.querySelectorAll('.tree-toggle[data-node^="sub-"], .tree-toggle[data-node^="dept-"]');
    subAndDeptNodes.forEach(node => {
        const nodeId = node.dataset.node;
        toggleNode(nodeId, false);
    });
}

/**
 * 🔍 Функция для быстрого поиска в локальном хранилище
 * Позволяет искать элементы, которые уже загружены на страницу
 * @param {string} selector - CSS-селектор, определяющий, где искать
 * @param {string} searchText - Текст для поиска
 * @param {string} itemSelector - CSS-селектор для определения элементов
 */
function quickLocalSearch(selector, searchText, itemSelector) {
    const container = document.querySelector(selector);
    if (!container) return;

    const searchQuery = searchText.toLowerCase();
    const items = container.querySelectorAll(itemSelector);

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const visible = text.includes(searchQuery);
        item.style.display = visible ? '' : 'none';
    });
}

/**
 * 🔄 Функция для обновления отчетов и статистики
 * @param {string} containerSelector - CSS-селектор контейнера для обновления
 * @param {string} url - URL для загрузки данных
 * @param {Object} params - Параметры запроса
 */
function updateReportData(containerSelector, url, params = {}) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    // Показываем индикатор загрузки
    container.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Загрузка данных...</p></div>';

    // Загружаем данные
    $.ajax({
        url: url,
        data: params,
        method: 'GET',
        success: function(response) {
            container.innerHTML = response;
        },
        error: function(error) {
            container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки данных: ${error.statusText}</div>`;
        }
    });
}

/**
 * 📊 Функция для экспорта данных
 * @param {string} url - URL для экспорта
 * @param {string} format - Формат экспорта (csv, xlsx, pdf)
 * @param {Object} filters - Фильтры для экспорта
 */
function exportData(url, format, filters = {}) {
    // Формируем параметры запроса
    const params = new URLSearchParams(filters);
    params.append('format', format);

    // Создаем URL для экспорта
    const exportUrl = `${url}?${params.toString()}`;

    // Открываем URL в новой вкладке или инициируем скачивание
    window.open(exportUrl, '_blank');
}