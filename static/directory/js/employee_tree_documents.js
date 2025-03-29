/**
 * Скрипт для управления выбором сотрудников и генерацией документов
 */
document.addEventListener('DOMContentLoaded', function() {
    // Находим кнопку для генерации документов
    const generateDocumentsBtn = document.getElementById('generate-documents-btn');
    
    // Массив для хранения выбранных сотрудников
    let selectedEmployees = [];
    
    // Добавляем обработчики к чекбоксам сотрудников
    const employeeCheckboxes = document.querySelectorAll('input.action-select');
    employeeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedEmployees();
        });
    });
    
    // Обновление списка выбранных сотрудников
    function updateSelectedEmployees() {
        selectedEmployees = [];
        
        // Собираем ID выбранных сотрудников
        document.querySelectorAll('input.action-select:checked').forEach(checkbox => {
            selectedEmployees.push(checkbox.value);
        });
        
        // Показываем или скрываем кнопку генерации документов
        if (selectedEmployees.length > 0) {
            generateDocumentsBtn.style.display = 'inline-block';
        } else {
            generateDocumentsBtn.style.display = 'none';
        }
        
        // Обновляем текст кнопки в зависимости от количества выбранных сотрудников
        if (selectedEmployees.length === 1) {
            generateDocumentsBtn.textContent = '📄 Сгенерировать документы';
        } else {
            generateDocumentsBtn.textContent = `📄 Сгенерировать документы (${selectedEmployees.length})`;
        }
    }
    
    // Обработчик нажатия на кнопку генерации документов
    generateDocumentsBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (selectedEmployees.length === 0) {
            alert('Пожалуйста, выберите хотя бы одного сотрудника.');
            return;
        }
        
        if (selectedEmployees.length > 1) {
            alert('Пожалуйста, выберите только одного сотрудника для генерации документов.');
            return;
        }
        
        // Используем правильный URL для страницы выбора типа документа
        window.location.href = `/directory/documents/selection/${selectedEmployees[0]}/`;
    });
    
    // Обработчик для выбора всех сотрудников
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            
            // Устанавливаем состояние всех чекбоксов
            employeeCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            // Обновляем список выбранных сотрудников
            updateSelectedEmployees();
        });
    }
    
    // Инициализация при загрузке страницы
    updateSelectedEmployees();
});