// 🔍 Расширенный поиск по дереву

class TreeSearch {
    constructor(treeElement) {
        this.tree = treeElement;
        this.searchCache = new Map();
        this.debounceTimer = null;
    }

    // Поиск с подсветкой совпадений
    search(searchText) {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(() => {
            this._performSearch(searchText.toLowerCase());
        }, 300);
    }

    // Выполнение поиска
    _performSearch(searchText) {
        if (!searchText) {
            this._resetSearch();
            return;
        }

        this.tree.querySelectorAll('tr').forEach(row => {
            const nameCell = row.querySelector('.field-name');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();
            const cacheKey = `${text}_${searchText}`;

            let isMatch = this.searchCache.get(cacheKey);
            if (isMatch === undefined) {
                isMatch = this._matchText(text, searchText);
                this.searchCache.set(cacheKey, isMatch);
            }

            this._updateRowVisibility(row, isMatch, searchText);
        });
    }

    // Сброс поиска
    _resetSearch() {
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.remove('hidden-by-search', 'highlight-search');
        });
    }

    // Проверка совпадения текста
    _matchText(text, searchText) {
        return text.includes(searchText);
    }

    // Обновление видимости строки
    _updateRowVisibility(row, isMatch, searchText) {
        row.classList.toggle('hidden-by-search', !isMatch);
        row.classList.toggle('highlight-search', isMatch);

        if (isMatch) {
            this._showParents(row);
        }
    }

    // Показ родительских узлов
    _showParents(row) {
        let parentId = row.dataset.parentId;
        while (parentId) {
            const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
            if (!parentRow) break;

            parentRow.classList.remove('hidden-by-search');
            const toggleBtn = parentRow.querySelector('.toggle-btn');
            if (toggleBtn && toggleBtn.dataset.state === 'collapsed') {
                toggleBtn.click();
            }

            parentId = parentRow.dataset.parentId;
        }
    }
}

// Инициализация поиска
document.addEventListener('DOMContentLoaded', function() {
    const tree = document.querySelector('#result_list tbody');
    const searchInput = document.querySelector('.tree-search');
    
    if (tree && searchInput) {
        const treeSearch = new TreeSearch(tree);
        searchInput.addEventListener('input', (e) => {
            treeSearch.search(e.target.value);
        });
    }
});