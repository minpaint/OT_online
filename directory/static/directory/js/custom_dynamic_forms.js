// Утилиты для отображения индикатора загрузки
const utils = {
    showLoading: function (element) {
        $(element).prop('disabled', true)
            .append('<span class="spinner-border spinner-border-sm ms-1" role="status" aria-hidden="true"></span>');
    },
    hideLoading: function (element) {
        $(element).prop('disabled', false).find('.spinner-border').remove();
    }
};

// Функции обновления списков
const updaters = {
    subdivisions: function (organizationId, targetSelect) {
        utils.showLoading(targetSelect);

        $.ajax({
            url: '/api/subdivisions/',
            data: {organization: organizationId},
            success: function (data) {
                let options = '<option value="">Выберите подразделение</option>';
                data.forEach(item => {
                    options += `<option value="${item.id}">${item.name}</option>`;
                });
                $(targetSelect).html(options).prop('disabled', false);
                $(targetSelect).trigger('change');
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке подразделений:', error);
                $(targetSelect).html('<option value="">Ошибка загрузки</option>').prop('disabled', false);
            },
            complete: function () {
                utils.hideLoading(targetSelect);
            }
        });
    },

    departments: function (organizationId, subdivisionId, targetSelect) {
        utils.showLoading(targetSelect);

        $.ajax({
            url: '/api/departments/',
            data: {organization: organizationId, subdivision: subdivisionId},
            success: function (data) {
                let options = '<option value="">Выберите отдел</option>';
                data.forEach(item => {
                    options += `<option value="${item.id}">${item.name}</option>`;
                });
                $(targetSelect).html(options).prop('disabled', false);
                $(targetSelect).trigger('change');
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке отделов:', error);
                $(targetSelect).html('<option value="">Ошибка загрузки</option>').prop('disabled', false);
            },
            complete: function () {
                utils.hideLoading(targetSelect);
            }
        });
    },

    positions: function (organizationId, subdivisionId, departmentId, targetSelect) {
        utils.showLoading(targetSelect);

        $.ajax({
            url: '/api/positions/',
            data: {organization: organizationId, subdivision: subdivisionId, department: departmentId},
            success: function (data) {
                let options = '<option value="">Выберите должность</option>';
                data.forEach(item => {
                    options += `<option value="${item.id}">${item.position_name}</option>`;
                });
                $(targetSelect).html(options).prop('disabled', false);
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке должностей:', error);
                $(targetSelect).html('<option value="">Ошибка загрузки</option>').prop('disabled', false);
            },
            complete: function () {
                utils.hideLoading(targetSelect);
            }
        });
    }
};

$(document).ready(function () {
    const $organization = $('#id_organization');
    const $subdivision = $('#id_subdivision');
    const $department = $('#id_department');
    const $position = $('#id_position');

    // Обработчики изменения селектов
    $organization.change(function () {
        const organizationId = $(this).val();
        updaters.subdivisions(organizationId, '#id_subdivision');
        $('#id_department').html('<option value="">---------</option>').prop('disabled', true);
        $('#id_position').html('<option value="">---------</option>').prop('disabled', true);
    });

    $subdivision.change(function () {
        const organizationId = $organization.val();
        const subdivisionId = $(this).val();
        updaters.departments(organizationId, subdivisionId, '#id_department');
        $('#id_position').html('<option value="">---------</option>').prop('disabled', true);
    });

    $department.change(function () {
        const organizationId = $organization.val();
        const subdivisionId = $subdivision.val();
        const departmentId = $(this).val();
        updaters.positions(organizationId, subdivisionId, departmentId, '#id_position');
    });

    // Инициализация при загрузке
    if ($organization.val()) {
        $organization.trigger('change');
    }

    if ($subdivision.val()) {
        $subdivision.trigger('change');
    }

    if ($department.val()) {
        $department.trigger('change');
    }
});
