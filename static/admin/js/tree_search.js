/**
 * 🔍 Улучшенный поиск по дереву
 */
class TreeSearch {
    constructor(treeElement) {
        this.tree = treeElement;
        this.searchCache = new Map();
        this.debounceTimer = null;
        this.lastSearchTerm = '';
    }

    search(searchText) {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(() => {
            this._performSearch(searchText.toLowerCase().trim());
        }, 200);
    }

    _performSearch(searchText) {
        if (!searchText) {
            this._resetSearch();
            return;
        }

        if (this.lastSearchTerm === searchText) {
            return;
        }

        this.lastSearchTerm = searchText;

        // Сначала скрываем все строки
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Ищем совпадения
        this.tree.querySelectorAll('tr').forEach(row => {
            const searchableContent = this._getSearchableContent(row);
            const hasMatch = searchableContent.includes(searchText);

            if (hasMatch) {
                this._showMatchedRow(row);
            }
        });
    }

    _getSearchableContent(row) {
        const searchableParts = [];

        // Ищем в названии
        const nameCell = row.querySelector('.field-name');
        if (nameCell) {
            searchableParts.push(nameCell.textContent);
        }

        // Ищем в ролях
        const rolesCell = row.querySelector('.field-roles');
        if (rolesCell) {
            // Получаем текст из title атрибутов
            rolesCell.querySelectorAll('[title]').forEach(el => {
                searchableParts.push(el.getAttribute('title'));
            });
            searchableParts.push(rolesCell.textContent);
        }

        return searchableParts.join(' ').toLowerCase();
    }

    _showMatchedRow(row) {
        // Показываем найденную строку
        row.classList.remove('hidden-by-search');
        row.classList.add('highlight-search');

        // Показываем и разворачиваем родителей
        this._showParents(row);
    }

    _showParents(row) {
        let parentId = row.dataset.parentId;

        while (parentId) {
            const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
            if (!parentRow) break;

            // Показываем родителя
            parentRow.classList.remove('hidden-by-search');

            // Разворачиваем узел
            const toggleBtn = parentRow.querySelector('.toggle-btn');
            if (toggleBtn) {
                if (toggleBtn.getAttribute('data-state') === 'collapsed') {
                    toggleBtn.setAttribute('data-state', 'expanded');
                    toggleBtn.textContent = '[-]';

                    // Показываем дочерние элементы
                    const nodeId = parentRow.dataset.nodeId;
                    if (nodeId) {
                        this.tree.querySelectorAll(`tr[data-parent-id="${nodeId}"]`)
                            .forEach(child => {
                                child.classList.remove('tree-row-hidden');
                            });
                    }
                }
            }

            parentId = parentRow.dataset.parentId;
        }
    }

    _resetSearch() {
        if (this.lastSearchTerm === '') return;

        this.lastSearchTerm = '';
        this.searchCache.clear();

        this.tree.querySelectorAll('tr').forEach(row => {
            // Убираем классы поиска
            row.classList.remove('hidden-by-search', 'highlight-search');
        });
    }
}

// Инициализация поиска
document.addEventListener('DOMContentLoaded', () => {
    const treeTable = document.getElementById('result_list');
    const searchInput = document.querySelector('.tree-search');

    if (treeTable && searchInput) {
        const treeSearch = new TreeSearch(treeTable);

        searchInput.addEventListener('input', (e) => {
            treeSearch.search(e.target.value);
        });

        // Очистка поиска по Escape
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                treeSearch.search('');
            }
        });
    }
});