(function($) {
    'use strict';

    // Универсальная функция для обновления зависимого списка.
    function updateSelect(url, data, childSelect) {
        if (!data || Object.keys(data).length === 0) {
            childSelect.html('<option value="">---------</option>');
            childSelect.prop('disabled', true);
            return;
        }
        $.ajax({
            url: url,
            type: 'GET',
            data: data,
            success: function(response) {
                let options = '<option value="">---------</option>';
                response.forEach(function(item) {
                    let displayName = item.name ? item.name :
                                      (item.position_name ? item.position_name : item.equipment_name);
                    options += `<option value="${item.id}">${displayName}</option>`;
                });
                childSelect.html(options);
                childSelect.prop('disabled', false);
            },
            error: function(error) {
                console.error('Error fetching data:', error);
                childSelect.html('<option value="">---------</option>');
                childSelect.prop('disabled', true);
            }
        });
    }

    $(document).ready(function() {
        // При выборе организации обновляем подразделения.
        $('#id_organization').change(function() {
            let organizationId = $(this).val();
            updateSelect('/directory/ajax/subdivisions/', { organization: organizationId }, $('#id_subdivision'));
            // Сбрасываем отделы и должности.
            $('#id_department').html('<option value="">---------</option>').prop('disabled', true);
            $('#id_position').html('<option value="">---------</option>').prop('disabled', true);
        });

        // При выборе структурного подразделения обновляем отделы.
        $('#id_subdivision').change(function() {
            let organizationId = $('#id_organization').val();
            let subdivisionId = $(this).val();
            updateSelect('/directory/ajax/departments/', { organization: organizationId, subdivision: subdivisionId }, $('#id_department'));
            // Сбрасываем должности.
            $('#id_position').html('<option value="">---------</option>').prop('disabled', true);
        });

        // При выборе отдела обновляем должности.
        $('#id_department').change(function() {
            let organizationId = $('#id_organization').val();
            let subdivisionId = $('#id_subdivision').val();
            let departmentId = $(this).val();
            let data = { organization: organizationId, subdivision: subdivisionId };
            if (departmentId) {
                data.department = departmentId;
            }
            updateSelect('/directory/ajax/positions/', data, $('#id_position'));
        });

        // Инициализация при загрузке, если значения уже выбраны.
        if ($('#id_organization').val()) {
            $('#id_organization').trigger('change');
            setTimeout(function() {
                if ($('#id_subdivision').val()) {
                    $('#id_subdivision').trigger('change');
                }
            }, 100);
        }
    });
})(django.jQuery);
