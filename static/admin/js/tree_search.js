/**
 * 🔍 Класс для поиска по древовидному списку
 * Работает как в админке, так и на основном сайте
 */
class TreeSearch {
    constructor(treeElement) {
        // 🌳 Элемент дерева
        this.tree = treeElement;
        // 💾 Кэш для хранения результатов поиска
        this.searchCache = new Map();
        // ⏲️ Таймер для debounce
        this.debounceTimer = null;
        // 📝 Последний поисковый запрос
        this.lastSearchTerm = '';
        // 🔄 Определение режима (админка или основной сайт)
        this.isAdminMode = this.tree.id === 'result_list';
    }

    /**
     * 🔎 Поиск с debounce
     */
    search(searchText) {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(() => {
            this._performSearch(searchText.toLowerCase().trim());
        }, 300);
    }

    /**
     * 🎯 Выполнение поиска
     */
    _performSearch(searchText) {
        // Если поисковый запрос пустой - сбрасываем поиск
        if (!searchText) {
            this._resetSearch();
            return;
        }

        // Если поисковый запрос не изменился - пропускаем
        if (this.lastSearchTerm === searchText) {
            return;
        }

        this.lastSearchTerm = searchText;

        // Скрываем ВСЕ строки сначала
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Массив для хранения найденных сотрудников
        const foundEmployees = [];

        // Ищем совпадения только среди элементов, которые представляют сотрудников
        this.tree.querySelectorAll('tr').forEach(row => {
            // Определяем, является ли строка сотрудником
            let isEmployee = false;

            if (this.isAdminMode) {
                // В админке сотрудники имеют чекбокс .action-select
                isEmployee = row.querySelector('.action-select') !== null;
            } else {
                // На основном сайте сотрудники имеют чекбокс .employee-checkbox
                isEmployee = row.querySelector('.employee-checkbox') !== null;

                // Дополнительно проверяем, не является ли это строкой организации/подразделения/отдела
                if (row.classList.contains('organization-row') ||
                    row.classList.contains('subdivision-row') ||
                    row.classList.contains('department-row')) {
                    isEmployee = false;
                }
            }

            if (!isEmployee) return;

            const nameCell = row.querySelector('.field-name') || row.querySelector('td:first-child');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();

            if (text.includes(searchText)) {
                // Это сотрудник, который соответствует поиску
                foundEmployees.push(row);
            }
        });

        // Показываем только найденных сотрудников
        foundEmployees.forEach(row => {
            row.classList.remove('hidden-by-search');
            row.classList.add('highlight-search');

            // Добавляем структурный путь, если его еще нет
            const nameCell = row.querySelector('.field-name') || row.querySelector('td:first-child');
            if (nameCell && !row.querySelector('.structure-path')) {
                const structurePath = this._getCleanPathToParents(row);

                // Добавляем путь только если он не пустой и его еще нет в отображении
                if (structurePath && !nameCell.textContent.includes(structurePath)) {
                    const pathSpan = document.createElement('span');
                    pathSpan.className = 'structure-path';
                    pathSpan.style.color = '#666';
                    pathSpan.style.marginLeft = '5px';
                    pathSpan.textContent = `(${structurePath})`;
                    nameCell.appendChild(pathSpan);
                }
            }
        });

        // Если ничего не найдено, показываем сообщение
        if (foundEmployees.length === 0) {
            const noResultsMsg = document.getElementById('no-search-results');
            if (noResultsMsg) {
                noResultsMsg.classList.remove('hidden-by-search');
            } else {
                // Создаем сообщение, если его нет
                const msgRow = document.createElement('tr');
                msgRow.id = 'no-search-results';
                msgRow.innerHTML = `<td colspan="5" class="text-center p-3">По запросу "${searchText}" ничего не найдено</td>`;
                this.tree.querySelector('tbody').appendChild(msgRow);
            }
        } else if (document.getElementById('no-search-results')) {
            document.getElementById('no-search-results').classList.add('hidden-by-search');
        }
    }

    /**
     * 👨‍👩‍👧‍👦 Показать родительские элементы найденного элемента
     */
    _showParents(row) {
        // Определяем атрибут родителя в зависимости от режима
        let parentAttr = this.isAdminMode ? 'parentId' : 'parent';
        let parentId = row.dataset[parentAttr];

        while (parentId) {
            // Определяем селектор для родителя
            const parentSelector = this.isAdminMode
                ? `tr[data-node-id="${parentId}"]`
                : `tr[data-node-id="${parentId}"]`;

            const parentRow = this.tree.querySelector(parentSelector);
            if (!parentRow) break;

            // Показываем родителя
            parentRow.classList.remove('hidden-by-search');

            // Определяем, как получить следующего родителя
            parentId = this.isAdminMode
                ? parentRow.dataset.parentId
                : parentRow.dataset.parent;

            // Раскрываем родителя, если он свернут
            if (this.isAdminMode) {
                const toggleBtn = parentRow.querySelector('.toggle-btn');
                if (toggleBtn && toggleBtn.getAttribute('data-state') === 'collapsed') {
                    toggleBtn.setAttribute('data-state', 'expanded');
                    toggleBtn.textContent = '[-]';

                    // Показываем детей
                    const childRows = this.tree.querySelectorAll(`tr[data-parent-id="${parentRow.dataset.nodeId}"]`);
                    childRows.forEach(child => {
                        child.classList.remove('tree-row-hidden');
                    });
                }
            } else {
                const toggleBtn = parentRow.querySelector('.tree-toggle');
                if (toggleBtn && toggleBtn.textContent === '+') {
                    toggleBtn.textContent = '-';

                    // Показываем детей
                    const childNodeId = parentRow.dataset.nodeId;
                    const children = this.tree.querySelectorAll(`tr[data-parent="${childNodeId}"]`);
                    children.forEach(child => {
                        child.classList.remove('tree-hidden');
                    });
                }
            }
        }
    }

    /**
     * 📍 Получение чистого пути до родительских элементов
     */
    _getCleanPathToParents(row) {
        const path = [];

        // Определяем атрибуты в зависимости от режима
        let parentAttr = this.isAdminMode ? 'parentId' : 'parent';
        let nodeAttr = this.isAdminMode ? 'nodeId' : 'nodeId';

        let parentId = row.dataset[parentAttr];

        while (parentId) {
            // Определяем селектор для родителя
            const parentSelector = this.isAdminMode
                ? `tr[data-node-id="${parentId}"]`
                : `tr[data-node-id="${parentId}"]`;

            const parentRow = this.tree.querySelector(parentSelector);
            if (!parentRow) break;

            const parentNameCell = parentRow.querySelector('.field-name') || parentRow.querySelector('td:first-child');
            if (parentNameCell) {
                // Получаем название родителя из strong тега, если он есть
                const strongElement = parentNameCell.querySelector('strong');
                let parentName = '';

                if (strongElement) {
                    parentName = strongElement.textContent.trim();
                } else {
                    // Если нет strong, берем весь текст и очищаем от управляющих символов
                    parentName = parentNameCell.textContent.replace(/[-+\[\]]/g, '').trim();
                }

                if (parentName) {
                    path.unshift(parentName); // Добавляем в начало массива
                }
            }

            // Переходим к следующему родителю
            parentId = this.isAdminMode
                ? parentRow.dataset.parentId
                : parentRow.dataset.parent;
        }

        if (path.length === 0) {
            return '';
        }

        return path.join(' → ');
    }

    /**
     * 🔄 Сброс поиска
     */
    _resetSearch() {
        if (this.lastSearchTerm === '') return;

        this.lastSearchTerm = '';
        this.searchCache.clear();

        // Удаляем сообщение о отсутствии результатов, если оно есть
        const noResultsMsg = document.getElementById('no-search-results');
        if (noResultsMsg) {
            noResultsMsg.remove();
        }

        // Возвращаем исходный вид для всех строк
        this.tree.querySelectorAll('tr').forEach(row => {
            // Убираем классы поиска
            row.classList.remove('hidden-by-search', 'highlight-search');

            // Удаляем добавленный путь структуры
            const structurePath = row.querySelector('.structure-path');
            if (structurePath) {
                structurePath.remove();
            }
        });

        // Восстанавливаем структуру дерева (показываем только те узлы, которые были раскрыты)
        this._restoreTreeState();
    }

    /**
     * 🔄 Восстановление состояния дерева после поиска
     * Показывает только те узлы, которые были раскрыты до поиска
     */
    _restoreTreeState() {
        // В разных режимах используются разные классы
        if (this.isAdminMode) {
            // Для админки используется .tree-row-hidden для скрытых узлов
            // Сначала скрываем все узлы с data-parent-id
            this.tree.querySelectorAll('tr[data-parent-id]').forEach(row => {
                const parentId = row.dataset.parentId;
                const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);

                if (parentRow) {
                    const toggleBtn = parentRow.querySelector('.toggle-btn');
                    if (toggleBtn && toggleBtn.getAttribute('data-state') === 'collapsed') {
                        row.classList.add('tree-row-hidden');
                    } else {
                        row.classList.remove('tree-row-hidden');
                    }
                }
            });
        } else {
            // Для основного сайта используется .tree-hidden для скрытых узлов
            // Обрабатываем узлы организаций
            this.tree.querySelectorAll('tr[data-node-id^="org-"]').forEach(orgRow => {
                const toggleEl = orgRow.querySelector('.tree-toggle');
                if (!toggleEl) return;

                const isExpanded = toggleEl.textContent === '-';
                const orgId = orgRow.dataset.nodeId;

                // Обрабатываем подразделения и отделы
                this.tree.querySelectorAll(`tr[data-parent="${orgId}"]`).forEach(subRow => {
                    if (!isExpanded) {
                        subRow.classList.add('tree-hidden');
                    } else {
                        // Проверяем, является ли подразделение раскрытым
                        const subToggleEl = subRow.querySelector('.tree-toggle');
                        if (subToggleEl) {
                            const subIsExpanded = subToggleEl.textContent === '-';
                            const subId = subRow.dataset.nodeId;

                            // Обрабатываем отделы и сотрудников подразделения
                            this.tree.querySelectorAll(`tr[data-parent="${subId}"]`).forEach(deptRow => {
                                if (!subIsExpanded) {
                                    deptRow.classList.add('tree-hidden');
                                } else {
                                    // Проверяем, является ли отдел раскрытым
                                    const deptToggleEl = deptRow.querySelector('.tree-toggle');
                                    if (deptToggleEl) {
                                        const deptIsExpanded = deptToggleEl.textContent === '-';
                                        const deptId = deptRow.dataset.nodeId;

                                        // Обрабатываем сотрудников отдела
                                        this.tree.querySelectorAll(`tr[data-parent="${deptId}"]`).forEach(empRow => {
                                            if (!deptIsExpanded) {
                                                empRow.classList.add('tree-hidden');
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }
                });
            });
        }
    }
}

// 🚀 Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Пытаемся найти таблицу дерева (сначала в админке, потом на основном сайте)
    const treeTable = document.getElementById('result_list') || document.getElementById('employeeTree');

    // Ищем поле поиска
    const searchInput = document.querySelector('.tree-search') || document.getElementById('localSearchInput');

    if (treeTable && searchInput) {
        const treeSearch = new TreeSearch(treeTable);

        // Обработка ввода в поле поиска
        searchInput.addEventListener('input', (e) => {
            treeSearch.search(e.target.value);
        });

        // Обработка клавиш в поле поиска
       searchInput.addEventListener('keydown', (e) => {
           if (e.key === 'Enter') {
               treeSearch.search(searchInput.value);
           } else if (e.key === 'Escape') {
               searchInput.value = '';
               treeSearch.search('');
           }
       });

       // Обработка кнопки поиска, если она есть
       const searchButton = document.getElementById('localSearchBtn');
       if (searchButton) {
           searchButton.addEventListener('click', () => {
               treeSearch.search(searchInput.value);
           });
       }

       // Обработка кнопки очистки, если она есть
       const clearButton = document.getElementById('clearSearchBtn');
       if (clearButton) {
           clearButton.addEventListener('click', () => {
               searchInput.value = '';
               treeSearch.search('');
           });
       }
   }
});