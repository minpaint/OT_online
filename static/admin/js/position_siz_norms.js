(function($) {
    $(document).ready(function() {
        // Функция для обновления select2 полей в динамически добавленной форме
        function initializeSelect2(container) {
            if ($.fn.select2) {
                $(container).find('.select2-hidden-accessible').each(function() {
                    var $select = $(this);
                    var options = {};
                    if ($select.data('autocomplete-light-url')) {
                        options.ajax = {
                            url: $select.data('autocomplete-light-url'),
                            dataType: 'json',
                            delay: 250,
                            data: function(params) {
                                return {
                                    q: params.term,
                                    page: params.page || 1
                                };
                            },
                            processResults: function(data, params) {
                                params.page = params.page || 1;
                                return {
                                    results: data.results,
                                    pagination: {
                                        more: data.more
                                    }
                                };
                            },
                            cache: true
                        };
                    }
                    $select.select2(options);
                });
            }
        }

        // Обработчик клика по кнопке "Добавить новую норму СИЗ"
        $('.add-siz-norm').on('click', function(e) {
            e.preventDefault();
            var formsetPrefix = $(this).closest('.js-inline-admin-formset').data('inline-formset').prefix;
            var totalForms = $('#id_' + formsetPrefix + '-TOTAL_FORMS');
            var newId = parseInt(totalForms.val());

            // Клонируем пустую форму
            var emptyForm = $('#' + formsetPrefix + '-empty').clone(true);
            emptyForm.removeClass('empty-form');
            emptyForm.attr('id', formsetPrefix + '-' + newId);

            // Обновляем ID и name атрибуты
            emptyForm.find(':input').each(function() {
                if ($(this).attr('id')) {
                    $(this).attr('id', $(this).attr('id').replace('-empty-', '-' + newId + '-'));
                }
                if ($(this).attr('name')) {
                    $(this).attr('name', $(this).attr('name').replace('-empty-', '-' + newId + '-'));
                }
            });

            // Добавляем новую форму перед пустой
            emptyForm.insertBefore($('#' + formsetPrefix + '-empty')).show();

            // Обновляем счетчик форм
            totalForms.val(newId + 1);

            // Инициализируем select2 для новых полей, если они используются
            initializeSelect2(emptyForm);

            // Обновляем классы строк
            $('#' + formsetPrefix + '-group tbody tr:visible').each(function(index) {
                $(this).removeClass('row1 row2').addClass(index % 2 === 0 ? 'row1' : 'row2');
            });
        });

        // Функция для автозаполнения полей при выборе СИЗ
        function setupSizChangeHandlers() {
            $('.field-siz select').on('change', function() {
                var row = $(this).closest('tr');
                var sizId = $(this).val();

                if (sizId) {
                    // Загружаем информацию о СИЗ через AJAX
                    $.get('/directory/api/siz/' + sizId + '/', function(data) {
                        // Обновляем поля с информацией о СИЗ
                        row.find('.field-classification input, .field-classification p').text(data.classification);
                        row.find('.field-unit input, .field-unit p').text(data.unit);
                        row.find('.field-wear_period input, .field-wear_period p').text(
                            data.wear_period === 0 ? 'До износа' : data.wear_period + ' мес.'
                        );
                    });
                }
            });
        }

        // Настраиваем обработчики при загрузке страницы
        setupSizChangeHandlers();
    });
})(django.jQuery);