(function($) {
    'use strict';

    function updateSelect(url, parentValue, childSelect, additionalData = {}) {
        if (!parentValue) {
            childSelect.html('<option value="">---------</option>');
            childSelect.prop('disabled', true);
            return;
        }

        $.ajax({
            url: url,
            data: { ...additionalData },
            success: function(data) {
                let options = '<option value="">---------</option>';
                data.forEach(function(item) {
                    const name = item.position_name || item.name || item.equipment_name;
                    options += `<option value="${item.id}">${name}</option>`;
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
        // Обработчик изменения организации
        $('#id_organization').change(function() {
            const organizationId = $(this).val();
            const data = { organization: organizationId };

            // Обновляем подразделения
            updateSelect('/directory/ajax/subdivisions/', organizationId, $('#id_subdivision'), data);

            // Сбрасываем зависимые поля
            $('#id_department').html('<option value="">---------</option>').prop('disabled', true);
            $('#id_position').html('<option value="">---------</option>').prop('disabled', true);

            // Очищаем множественные поля если они есть
            if ($('#id_documents').length) {
                $('#id_documents').val([]);
            }
            if ($('#id_equipment').length) {
                $('#id_equipment').val([]);
            }
        });

        // Обработчик изменения подразделения
        $('#id_subdivision').change(function() {
            const subdivisionId = $(this).val();
            const organizationId = $('#id_organization').val();
            const data = {
                subdivision: subdivisionId,
                organization: organizationId
            };

            // Обновляем отделы
            updateSelect('/directory/ajax/departments/', subdivisionId, $('#id_department'), data);

            // Сбрасываем зависимые поля
            $('#id_position').html('<option value="">---------</option>').prop('disabled', true);

            // Обновляем документы и оборудование если они есть
            if ($('#id_documents').length) {
                updateSelect('/directory/ajax/documents/', subdivisionId, $('#id_documents'), data);
            }
            if ($('#id_equipment').length) {
                updateSelect('/directory/ajax/equipment/', subdivisionId, $('#id_equipment'), data);
            }
        });

        // Обработчик изменения отдела
        $('#id_department').change(function() {
            const departmentId = $(this).val();
            const organizationId = $('#id_organization').val();
            const subdivisionId = $('#id_subdivision').val();
            const data = {
                department: departmentId,
                organization: organizationId,
                subdivision: subdivisionId
            };

            // Обновляем должности
            if ($('#id_position').length) {
                updateSelect('/directory/ajax/positions/', departmentId, $('#id_position'), data);
            }

            // Обновляем документы и оборудование если они есть
            if ($('#id_documents').length) {
                updateSelect('/directory/ajax/documents/', departmentId, $('#id_documents'), data);
            }
            if ($('#id_equipment').length) {
                updateSelect('/directory/ajax/equipment/', departmentId, $('#id_equipment'), data);
            }
        });

        // Инициализация при загрузке страницы
        if ($('#id_organization').val()) {
            $('#id_organization').trigger('change');
            // Если есть выбранное подразделение, тригерим и его изменение
            setTimeout(function() {
                if ($('#id_subdivision').val()) {
                    $('#id_subdivision').trigger('change');
                }
            }, 100);
        }
    });
})(django.jQuery);