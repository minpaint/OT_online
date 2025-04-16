// static/admin/js/commission_admin.js
(function($) {
    $(document).ready(function() {
        // Функция для обновления полей, зависящих от организации
        function updateDependentFields(organizationSelect) {
            var organizationId = organizationSelect.val();
            var $subdivisionField = $('#id_subdivision');
            var $departmentField = $('#id_department');

            // Очищаем зависимые поля, если организация не выбрана
            if (!organizationId) {
                $subdivisionField.val('').trigger('change');
                $departmentField.val('').trigger('change');
                return;
            }

            // Обновляем поле подразделения - это автоматически
            // делается через автодополнение с forward параметром
        }

        // Обработчики событий изменения полей
        $('#id_organization').on('change', function() {
            updateDependentFields($(this));
        });

        $('#id_subdivision').on('change', function() {
            var subdivisionId = $(this).val();
            var $departmentField = $('#id_department');

            // Очищаем отдел, если подразделение не выбрано
            if (!subdivisionId) {
                $departmentField.val('').trigger('change');
            }
            // Обновление отдела происходит автоматически через автодополнение
        });

        // Инициализация при загрузке страницы
        updateDependentFields($('#id_organization'));
    });
})(django.jQuery);