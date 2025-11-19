/**
 * 🔍 Класс для поиска в древовидной структуре
 * Модифицировано для работы с текущей структурой DOM
 */
class TreeSearch {
    constructor(treeElement) {
        // 🌳 Элемент дерева
        this.tree = treeElement || document.getElementById('employeeTree') || document.getElementById('result_list');
        // 💾 Кэш для хранения результатов поиска
        this.searchCache = new Map();
        // ⏲️ Таймер для debounce
        this.debounceTimer = null;
        // 📝 Последний поисковый запрос
        this.lastSearchTerm = '';

        // Инициализация обработчиков событий
        this.init();
    }

    /**
     * 🚀 Инициализация поискового модуля
     */
    init() {
        if (!this.tree) {
            console.log('❌ Дерево не найдено');
            return;
        }

        // Находим поле поиска и кнопки (сначала глобальные, потом локальные)
        const searchInput = document.getElementById('globalSearchInput') ||
                           document.getElementById('localSearchInput') ||
                           document.querySelector('.tree-search');
        const searchBtn = document.getElementById('globalSearchBtn') ||
                         document.getElementById('localSearchBtn');
        const clearBtn = document.getElementById('globalClearBtn') ||
                        document.getElementById('clearSearchBtn');

        if (!searchInput) {
            console.log('❌ Поле поиска не найдено');
            return;
        }

        // Сохраняем ссылку на поле поиска
        this.searchInput = searchInput;

        // Обработчик ввода в поле поиска
        searchInput.addEventListener('input', (e) => {
            this.search(e.target.value);
        });

        // Обработчик нажатия Enter
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.search(searchInput.value);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                searchInput.value = '';
                this.search('');
            }
        });

        // Обработчик кнопки поиска
        if (searchBtn) {
            searchBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.search(searchInput.value);
            });
        }

        // Обработчик кнопки очистки
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                searchInput.value = '';
                this.search('');
            });
        }

        console.log('✅ TreeSearch инициализирован');
    }

    /**
     * 🔎 Поиск с debounce
     * @param {string} searchText - Текст для поиска
     */
    search(searchText) {
        // Отменяем предыдущий таймер, если он есть
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Ставим новый таймер
        this.debounceTimer = setTimeout(() => {
            this._performSearch(searchText.toLowerCase().trim());
        }, 300);
    }

    /**
     * 🎯 Выполнение поиска
     * @param {string} searchText - Текст для поиска (уже в нижнем регистре)
     */
    _performSearch(searchText) {
        if (!this.tree) return;

        // Если поисковый запрос пустой - сбрасываем поиск
        if (!searchText) {
            this._resetSearch();
            return;
        }

        // Если поисковый запрос не изменился - пропускаем
        if (this.lastSearchTerm === searchText) {
            return;
        }

        console.log(`🔍 Выполняется поиск: "${searchText}"`);

        this.lastSearchTerm = searchText;

        // Проверяем кэш
        if (this.searchCache.has(searchText)) {
            const { foundRows } = this.searchCache.get(searchText);
            this._showResults(foundRows, searchText);
            return;
        }

        // Скрываем все строки
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.add('hidden-by-search');
            row.classList.remove('highlight-search');
        });

        // Массив для найденных сотрудников
        const foundRows = [];

        // Ищем совпадения среди сотрудников (строки с чекбоксами)
        this.tree.querySelectorAll('tr').forEach(row => {
            // Проверяем наличие чекбокса в строке (признак строки сотрудника)
            const hasCheckbox = row.querySelector('input[type="checkbox"]');
            if (!hasCheckbox) return;

            // Не рассматриваем строки организаций и подразделений
            if (row.classList.contains('organization-row') ||
                row.classList.contains('subdivision-row') ||
                row.classList.contains('department-row')) {
                return;
            }

            // Получаем текст ячейки с именем
            const nameCell = row.querySelector('.field-name');
            if (!nameCell) return;

            const text = nameCell.textContent.toLowerCase();
            if (text.includes(searchText)) {
                foundRows.push(row);
            }
        });

        // Кэшируем результаты
        this.searchCache.set(searchText, { foundRows });

        // Показываем результаты
        this._showResults(foundRows, searchText);
    }

    /**
     * 🔍 Отображение результатов поиска
     * @param {Array} foundRows - Массив найденных строк
     * @param {string} searchText - Текст поиска
     */
    _showResults(foundRows, searchText) {
        // Показываем найденных сотрудников и их родителей
        foundRows.forEach(row => {
            row.classList.remove('hidden-by-search');
            row.classList.add('highlight-search');

            // Показываем родительские элементы и разворачиваем их
            this._showParents(row);
        });

        // Обновляем сообщение о результатах поиска
        this._updateNoResultsMessage(foundRows.length === 0, searchText);

        console.log(`🔍 Найдено ${foundRows.length} совпадений`);
    }

    /**
     * 🔍 Показать родительские элементы найденного сотрудника
     * @param {HTMLElement} row - Строка сотрудника
     */
    _showParents(row) {
        // Получаем идентификатор родителя
        let parentId = row.getAttribute('data-parent');

        if (!parentId) return;

        // Итеративно поднимаемся по дереву, показывая родителей
        while (parentId) {
            const parentRow = this.tree.querySelector(`tr[data-node-id="${parentId}"]`);
            if (!parentRow) break;

            // Показываем родителя
            parentRow.classList.remove('hidden-by-search');

            // Разворачиваем родителя, если он свёрнут
            const toggle = parentRow.querySelector('.tree-toggle');
            if (toggle && toggle.textContent === '+') {
                // Изменяем текст переключателя
                toggle.textContent = '-';

                // Находим дочерние элементы и показываем их
                const children = this.tree.querySelectorAll(`tr[data-parent="${parentId}"]`);
                children.forEach(child => {
                    child.classList.remove('tree-hidden');
                });
            }

            // Переходим к следующему родителю
            parentId = parentRow.getAttribute('data-parent');
        }
    }

    /**
     * 🔍 Обновить сообщение об отсутствии результатов
     * @param {boolean} showMessage - Показывать ли сообщение
     * @param {string} searchText - Текст поиска
     */
    _updateNoResultsMessage(showMessage, searchText) {
        // Удаляем существующее сообщение
        const existingMsg = document.getElementById('no-search-results');
        if (existingMsg) {
            existingMsg.remove();
        }

        // Создаем новое сообщение, если нужно
        if (showMessage) {
            console.log(`🔍 Показываем сообщение: По запросу "${searchText}" ничего не найдено`);

            const msgRow = document.createElement('div');
            msgRow.id = 'no-search-results';
            msgRow.className = 'alert alert-warning mt-3';
            msgRow.innerHTML = `🔍 По запросу "<strong>${searchText}</strong>" ничего не найдено`;

            // Вставляем перед таблицей (деревом)
            if (this.tree.parentNode) {
                this.tree.parentNode.insertBefore(msgRow, this.tree);
            }
        }
    }

    /**
     * 🔄 Сброс поиска
     */
    _resetSearch() {
        if (!this.tree || this.lastSearchTerm === '') return;

        console.log('🔍 Сброс результатов поиска');

        this.lastSearchTerm = '';

        // Удаляем сообщение об отсутствии результатов
        const noResultsMsg = document.getElementById('no-search-results');
        if (noResultsMsg) {
            noResultsMsg.remove();
        }

        // Возвращаем исходный вид для всех строк
        this.tree.querySelectorAll('tr').forEach(row => {
            row.classList.remove('hidden-by-search', 'highlight-search');
        });

        // Восстанавливаем состояние дерева
        this._restoreTreeState();
    }

    /**
     * 🔄 Восстановить состояние дерева после сброса поиска
     */
    _restoreTreeState() {
        if (!this.tree) return;

        // Восстанавливаем состояние из глобального экземпляра TreeCore
        if (window.treeCore) {
            // Если есть инициализированный TreeCore, используем его для восстановления
            window.treeCore._restoreState();
            return;
        }

        // Иначе восстанавливаем состояние вручную
        // Проходим по всем переключателям
        this.tree.querySelectorAll('.tree-toggle').forEach(toggle => {
            const nodeId = toggle.getAttribute('data-node');
            if (!nodeId) return;

            const isExpanded = toggle.textContent === '-';

            // Если переключатель свёрнут, скрываем все его дочерние элементы
            if (!isExpanded) {
                const children = this.tree.querySelectorAll(`tr[data-parent="${nodeId}"]`);
                children.forEach(child => {
                    child.classList.add('tree-hidden');
                });
            }
        });
    }
}

// Автоинициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔄 DOM загружен, инициализируем TreeSearch');

    // Находим дерево
    const treeElement = document.getElementById('employeeTree') || document.getElementById('result_list');

    if (treeElement) {
        // Создаем экземпляр TreeSearch и сохраняем его в глобальной переменной
        window.treeSearch = new TreeSearch(treeElement);
    }
});