// Функция для обновления списка подразделений
function updateSubdivisions(organizationId, targetSelect) {
    if (!organizationId) {
        $(targetSelect).html('<option value="">---------</option>');
        return;
    }

    $.ajax({
        url: '/api/subdivisions/',
        data: { organization: organizationId },
        success: function(data) {
            let options = '<option value="">---------</option>';
            data.forEach(item => {
                options += `<option value="${item.id}">${item.name}</option>`;
            });
            $(targetSelect).html(options);
        }
    });
}

// Функция для обновления списка должностей
function updatePositions(subdivisionId, targetSelect) {
    if (!subdivisionId) {
        $(targetSelect).html('<option value="">---------</option>');
        return;
    }

    $.ajax({
        url: '/api/positions/',
        data: { subdivision: subdivisionId },
        success: function(data) {
            let options = '<option value="">---------</option>';
            data.forEach(item => {
                options += `<option value="${item.id}">${item.name}</option>`;
            });
            $(targetSelect).html(options);
        }
    });
}

// Инициализация всплывающих подсказок Bootstrap
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

// Автоматическое скрытие сообщений об успехе
$(document).ready(function() {
    setTimeout(function() {
        $('.alert-success').fadeOut('slow');
    }, 3000);
});

// Подтверждение удаления
function confirmDelete(event, message) {
    if (!confirm(message || 'Вы уверены, что хотите удалить этот элемент?')) {
        event.preventDefault();
    }
}