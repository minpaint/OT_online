/**
 * 🔍 Поиск по дереву
 * Показывает только найденные позиции со структурным путём
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

        // Сначала скрываем все строки
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Ищем совпадения только среди должностей
        this.tree.querySelectorAll('tr').forEach(row => {
            // Проверяем, что это строка с должностью (имеет checkbox)
            const hasCheckbox = row.querySelector('.action-select');
            if (!hasCheckbox) return;

            const nameCell = row.querySelector('.field-name');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();
            if (text.includes(searchText)) {
                // Показываем только строку с должностью
                row.classList.remove('hidden-by-search');
                row.classList.add('highlight-search');

                // Добавляем структурный путь, если его еще нет
                if (!row.querySelector('.structure-path')) {
                    const structurePath = this._getStructurePath(row);
                    const pathSpan = document.createElement('span');
                    pathSpan.className = 'structure-path';
                    pathSpan.style.color = '#666';
                    pathSpan.style.marginLeft = '5px';
                    pathSpan.textContent = `(${structurePath})`;
                    nameCell.appendChild(pathSpan);
                }
            }
        });
    }

    /**
     * 📍 Получение структурного пути
     */
    _getStructurePath(row) {
        const path = [];
        let currentRow = row;

        while (currentRow) {
            const parentId = currentRow.dataset.parentId;
            if (!parentId) break;

            const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
            if (!parentRow) break;

            const nameCell = parentRow.querySelector('.field-name');
            if (nameCell) {
                // Получаем только текст, убирая кнопки и иконки
                const name = nameCell.textContent.replace(/[$$$$\-\+]/g, '').trim();
                path.unshift(name);
            }

            currentRow = parentRow;
        }

        return path.join(' → ');
    }

    /**
     * 🔄 Сброс поиска
     */
    _resetSearch() {
        if (this.lastSearchTerm === '') return;

        this.lastSearchTerm = '';

        // Возвращаем исходный вид
        this.tree.querySelectorAll('tr').forEach(row => {
            // Убираем классы поиска
            row.classList.remove('hidden-by-search', 'highlight-search');

            // Удаляем добавленный путь структуры
            const structurePath = row.querySelector('.structure-path');
            if (structurePath) {
                structurePath.remove();
            }
        });
    }
}

// 🚀 Инициализация
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