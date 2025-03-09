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

        // Скрываем ВСЕ строки (включая структуру дерева)
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Ищем совпадения только среди элементов с чекбоксом
        this.tree.querySelectorAll('tr').forEach(row => {
            // Проверяем, что это строка с чекбоксом (элемент справочника)
            const hasCheckbox = row.querySelector('.action-select');
            if (!hasCheckbox) return;

            const nameCell = row.querySelector('.field-name');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();

            if (text.includes(searchText)) {
                // Показываем только строку с найденным элементом
                row.classList.remove('hidden-by-search');
                row.classList.add('highlight-search');

                // Добавляем структурный путь, если его еще нет
                if (!row.querySelector('.structure-path')) {
                    const structurePath = this._getCleanPathToParents(row);

                    // Добавляем путь только если он не пустой
                    if (structurePath) {
                        const pathSpan = document.createElement('span');
                        pathSpan.className = 'structure-path';
                        pathSpan.style.color = '#666';
                        pathSpan.style.marginLeft = '5px';
                        pathSpan.textContent = `(${structurePath})`;
                        nameCell.appendChild(pathSpan);
                    }
                }
            }
        });
    }

    /**
     * 📍 Получение чистого пути только к родительским элементам
     * Извлекает текст, игнорируя иконки и другие HTML-элементы
     */
    _getCleanPathToParents(row) {
        const path = [];

        let parentId = row.dataset.parentId;
        while (parentId) {
            const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
            if (!parentRow) break;

            const parentNameCell = parentRow.querySelector('.field-name');
            if (parentNameCell) {
                // Получаем чистый текст, игнорируя HTML-элементы
                let cleanText = '';

                // Обходим только текстовые узлы, игнорируя HTML
                for (let i = 0; i < parentNameCell.childNodes.length; i++) {
                    const node = parentNameCell.childNodes[i];
                    // Берем только текстовые узлы (тип 3)
                    if (node.nodeType === 3) {
                        cleanText += node.textContent;
                    }
                }

                // Если прямой обход не дает результата, используем fallback
                if (!cleanText.trim()) {
                    cleanText = parentNameCell.innerText;
                }

                // Очищаем текст от лишних символов
                cleanText = cleanText.replace(/\s+/g, ' ').trim();

                if (cleanText) {
                    path.push(cleanText);
                }
            }

            parentId = parentRow.dataset.parentId;
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

        // Обработка ввода в поле поиска
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