(function($) {
    'use strict';
    $(function() {
        const orgSelect = $('#id_organization');
        const deptSelect = $('#id_department');
        const divSelect = $('#id_division');

        // Функция очистки зависимого списка
        function clearSelect($select) {
            $select.empty().append($('<option value="">---------</option>'));
            $select.prop('disabled', true);
        }

        // Обновление списка подразделений
        function updateDepartments() {
            const orgId = orgSelect.val();
            clearSelect(deptSelect);
            clearSelect(divSelect);

            if (!orgId) return;

            $.get(`/api/organizations/${orgId}/departments/`)
                .done(function(data) {
                    deptSelect.prop('disabled', false);
                    data.forEach(function(dept) {
                        deptSelect.append(
                            $('<option></option>')
                                .attr('value', dept.id)
                                .text(dept.name)
                        );
                    });
                    // Если есть сохраненное значение, устанавливаем его
                    if (deptSelect.data('value')) {
                        deptSelect.val(deptSelect.data('value'));
                        deptSelect.trigger('change');
                    }
                });
        }

        // Обновление списка отделов
        function updateDivisions() {
            const deptId = deptSelect.val();
            clearSelect(divSelect);

            if (!deptId) return;

            $.get(`/api/departments/${deptId}/divisions/`)
                .done(function(data) {
                    divSelect.prop('disabled', false);
                    data.forEach(function(div) {
                        divSelect.append(
                            $('<option></option>')
                                .attr('value', div.id)
                                .text(div.name)
                        );
                    });
                    // Если есть сохраненное значение, устанавливаем его
                    if (divSelect.data('value')) {
                        divSelect.val(divSelect.data('value'));
                    }
                });
        }

        // Сохраняем начальные значения
        deptSelect.data('value', deptSelect.val());
        divSelect.data('value', divSelect.val());

        // Привязываем обработчики событий
        orgSelect.on('change', updateDepartments);
        deptSelect.on('change', updateDivisions);

        // Если есть выбранная организация, обновляем списки
        if (orgSelect.val()) {
            updateDepartments();
        }
    });
})(django.jQuery);