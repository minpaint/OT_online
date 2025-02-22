class TreeSearch {
    constructor(treeTable) {
        this.treeTable = treeTable;
        this.searchInput = document.querySelector('.tree-search');

        if (!this.searchInput || !this.treeTable) return;

        // Инициализация поиска
        this.initSearch();
    }

    initSearch() {
        let searchTimeout;

        // Добавляем обработчик ввода с debounce
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const searchText = e.target.value.trim().toLowerCase();
                this.performSearch(searchText);
            }, 300);
        });
    }

    performSearch(searchText) {
        // Получаем все строки таблицы
        const rows = Array.from(this.treeTable.querySelectorAll('tbody tr'));

        // Очищаем предыдущую подсветку
        this.clearHighlight(rows);

        if (!searchText) {
            // Если поиск пустой - показываем все строки
            rows.forEach(row => {
                row.classList.remove('tree-row-hidden');
                row.classList.remove('search-result');
            });
            return;
        }

        // Создаём множество для хранения ID видимых узлов
        const visibleNodes = new Set();

        // Первый проход - ищем совпадения
        rows.forEach(row => {
            const nameCell = row.querySelector('td.field-name');
            const rolesCell = row.querySelector('td.field-roles');

            if (!nameCell) return;

            const name = nameCell.textContent.toLowerCase();
            const roles = rolesCell ? rolesCell.textContent.toLowerCase() : '';

            // Проверяем совпадение в имени или ролях
            if (name.includes(searchText) || roles.includes(searchText)) {
                row.classList.add('search-result');
                this.highlightText(nameCell, searchText);
                if (rolesCell) {
                    this.highlightText(rolesCell, searchText);
                }

                // Добавляем текущий узел и его родителей в множество видимых
                this.addNodeAndParentsToVisible(row, visibleNodes);
            }
        });

        // Второй проход - обновляем видимость
        rows.forEach(row => {
            const nodeId = row.getAttribute('data-node-id');
            const isVisible = visibleNodes.has(nodeId) || row.classList.contains('search-result');

            if (isVisible) {
                row.classList.remove('tree-row-hidden');
                // Разворачиваем родительские узлы
                const toggleBtn = row.querySelector('.toggle-btn');
                if (toggleBtn) {
                    toggleBtn.setAttribute('data-state', 'expanded');
                    toggleBtn.textContent = '[-]';
                }
            } else {
                row.classList.add('tree-row-hidden');
            }
        });

        // Показываем количество найденных результатов
        this.showSearchResults(rows.filter(row => row.classList.contains('search-result')).length);
    }

    clearHighlight(rows) {
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach(cell => {
                cell.innerHTML = cell.innerHTML.replace(
                    /<mark class="search-highlight">(.*?)<\/mark>/g,
                    '$1'
                );
            });
        });
    }

    highlightText(element, searchText) {
        const content = element.innerHTML;
        const regex = new RegExp(`(${searchText})`, 'gi');
        element.innerHTML = content.replace(regex, '<mark class="search-highlight">$1</mark>');
    }

    addNodeAndParentsToVisible(row, visibleNodes) {
        let currentRow = row;
        while (currentRow) {
            const nodeId = currentRow.getAttribute('data-node-id');
            if (nodeId) {
                visibleNodes.add(nodeId);
            }

            const parentId = currentRow.getAttribute('data-parent-id');
            if (!parentId) break;

            currentRow = this.treeTable.querySelector(`tr[data-node-id="${parentId}"]`);
        }
    }

    showSearchResults(count) {
        let resultsInfo = document.getElementById('search-results-info');
        if (!resultsInfo) {
            resultsInfo = document.createElement('div');
            resultsInfo.id = 'search-results-info';
            this.searchInput.parentNode.appendChild(resultsInfo);
        }

        if (this.searchInput.value.trim()) {
            resultsInfo.textContent = `Найдено: ${count}`;
            resultsInfo.style.display = 'block';
        } else {
            resultsInfo.style.display = 'none';
        }
    }
}