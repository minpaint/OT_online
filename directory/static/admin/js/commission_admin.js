(function($) {
    'use strict';
    $(document).ready(function() {
        // Функция для обновления зависимых полей
        function updateFieldDependencies() {
            const organizationField = $('#id_organization');
            const subdivisionField = $('#id_subdivision');
            const departmentField = $('#id_department');

            // Первоначальное состояние: если нет значений, отключаем поля
            if (!organizationField.val()) {
                subdivisionField.prop('disabled', true);
                departmentField.prop('disabled', true);
            } else if (!subdivisionField.val()) {
                departmentField.prop('disabled', true);
            }

            // При изменении организации
            organizationField.on('change', function() {
                // Если выбрана организация
                if (organizationField.val()) {
                    subdivisionField.prop('disabled', false);
                    // Сбрасываем значения зависимых полей
                    subdivisionField.val(null).trigger('change');
                    departmentField.val(null).trigger('change');
                } else {
                    // Если организация очищена, блокируем подразделение и отдел
                    subdivisionField.prop('disabled', true);
                    departmentField.prop('disabled', true);
                    // Сбрасываем значения
                    subdivisionField.val(null).trigger('change');
                    departmentField.val(null).trigger('change');
                }
            });

            // При изменении подразделения
            subdivisionField.on('change', function() {
                // Если выбрано подразделение
                if (subdivisionField.val()) {
                    departmentField.prop('disabled', false);
                    // Сбрасываем значение отдела
                    departmentField.val(null).trigger('change');
                } else {
                    // Если подразделение очищено, блокируем отдел
                    departmentField.prop('disabled', true);
                    // Сбрасываем значение
                    departmentField.val(null).trigger('change');
                }
            });

            // Обеспечиваем взаимоисключение полей
            let lastChanged = null;

            organizationField.on('change', function() {
                if (organizationField.val() && lastChanged !== 'organization') {
                    lastChanged = 'organization';
                    // Если выбрали организацию, очищаем другие поля
                    if (subdivisionField.val() || departmentField.val()) {
                        subdivisionField.val(null).trigger('change');
                        departmentField.val(null).trigger('change');
                    }
                }
            });

            subdivisionField.on('change', function() {
                if (subdivisionField.val() && lastChanged !== 'subdivision') {
                    lastChanged = 'subdivision';
                    // Если выбрали подразделение, очищаем организацию и отдел
                    if (organizationField.val() || departmentField.val()) {
                        organizationField.val(null).trigger('change');
                        departmentField.val(null).trigger('change');
                    }
                }
            });

            departmentField.on('change', function() {
                if (departmentField.val() && lastChanged !== 'department') {
                    lastChanged = 'department';
                    // Если выбрали отдел, очищаем организацию
                    if (organizationField.val()) {
                        organizationField.val(null).trigger('change');
                    }
                }
            });
        }

        // Инициализация на странице редактирования комиссии
        if ($('#id_organization').length && $('#id_subdivision').length && $('#id_department').length) {
            // Визуальное выделение режима привязки
            const organizationGroup = $('#id_organization').closest('.form-group');
            const subdivisionGroup = $('#id_subdivision').closest('.form-group');
            const departmentGroup = $('#id_department').closest('.form-group');

            function updateGroupHighlighting() {
                const organizationVal = $('#id_organization').val();
                const subdivisionVal = $('#id_subdivision').val();
                const departmentVal = $('#id_department').val();

                // Сбрасываем все выделения
                organizationGroup.removeClass('border-primary bg-light');
                subdivisionGroup.removeClass('border-primary bg-light');
                departmentGroup.removeClass('border-primary bg-light');

                // Добавляем выделение активному полю
                if (organizationVal) {
                    organizationGroup.addClass('border-primary bg-light');
                } else if (subdivisionVal) {
                    subdivisionGroup.addClass('border-primary bg-light');
                } else if (departmentVal) {
                    departmentGroup.addClass('border-primary bg-light');
                }
            }

            // Обновляем выделение при изменении полей
            $('#id_organization, #id_subdivision, #id_department').on('change', updateGroupHighlighting);

            // Инициализация выделения и зависимостей
            updateGroupHighlighting();
            updateFieldDependencies();

            // Добавляем подсказку о взаимоисключении
            const helpText = $('<div class="alert alert-info mt-3">' +
                               '<i class="fas fa-info-circle"></i> ' +
                               'Комиссия должна быть привязана только к одному уровню: ' +
                               'организация, подразделение или отдел.' +
                               '</div>');
            $('#id_department').closest('.form-group').after(helpText);
        }

        // Инициализация на странице участника комиссии
        if ($('input[name="role"]').length) {
            // Подсветка выбранной роли
            $('input[name="role"]').change(function() {
                $('.role-selector .form-check').removeClass('bg-light');
                $(this).closest('.form-check').addClass('bg-light');
            });

            // Подсветка текущей выбранной роли
            $('input[name="role"]:checked').closest('.form-check').addClass('bg-light');
        }
    });
})(django.jQuery);