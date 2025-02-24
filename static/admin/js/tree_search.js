/**
 * 🔍 Поиск по дереву (локальный)
 */
class TreeSearch {
    constructor(treeElement) {
        this.tree = treeElement;
        this.debounceTimer = null;
        this.lastSearchTerm = '';
    }

    search(searchText) {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.debounceTimer = setTimeout(() => {
            this._performSearch(searchText.toLowerCase().trim());
        }, 300);
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

        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        this.tree.querySelectorAll('tr').forEach(row => {
            const hasCheckbox = row.querySelector('.action-select');
            if (!hasCheckbox) return;

            const nameCell = row.querySelector('.field-name');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();
            if (text.includes(searchText)) {
                row.classList.remove('hidden-by-search');
                row.classList.add('highlight-search');

                // Пробуждаем родителей
                let parentId = row.dataset.parentId;
                while (parentId) {
                    const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
                    if (parentRow) {
                        parentRow.classList.remove('hidden-by-search');
                        parentId = parentRow.dataset.parentId;
                    } else {
                        break;
                    }
                }
            }
        });
    }

    _resetSearch() {
        this.lastSearchTerm = '';
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.remove('hidden-by-search', 'highlight-search');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const treeTable = document.getElementById('result_list');
    const searchInput = document.querySelector('.tree-search');

    if (treeTable && searchInput) {
        const treeSearch = new TreeSearch(treeTable);

        searchInput.addEventListener('input', (e) => {
            treeSearch.search(e.target.value);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                treeSearch.search('');
            }
        });
    }
});
