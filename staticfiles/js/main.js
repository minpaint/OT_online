// Инициализация всплывающих подсказок Bootstrap
    document.addEventListener('DOMContentLoaded', function() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });

        // Автоматическое скрытие алертов
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    });

    // Подтверждение удаления
    function confirmDelete(event, itemName) {
        if (!confirm(`Вы уверены, что хотите удалить "${itemName}"?`)) {
            event.preventDefault();
            return false;
        }
        return true;
    }

    // Динамическая загрузка зависимых полей в формах
    function updateDepartments(organizationId, departmentSelect) {
        if (!organizationId) {
            departmentSelect.innerHTML = '<option value="">---------</option>';
            return;
        }

        fetch(`/api/organizations/${organizationId}/departments/`)
            .then(response => response.json())
            .then(data => {
                departmentSelect.innerHTML = '<option value="">---------</option>';
                data.forEach(dept => {
                    const option = new Option(dept.name, dept.id);
                    departmentSelect.add(option);
                });
            });
    }

    function updateDivisions(departmentId, divisionSelect) {
        if (!departmentId) {
            divisionSelect.innerHTML = '<option value="">---------</option>';
            return;
        }

        fetch(`/api/departments/${departmentId}/divisions/`)
            .then(response => response.json())
            .then(data => {
                divisionSelect.innerHTML = '<option value="">---------</option>';
                data.forEach(div => {
                    const option = new Option(div.name, div.id);
                    divisionSelect.add(option);
                });
            });
    }