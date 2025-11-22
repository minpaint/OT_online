# Periodic protocol implementation notes

## Что сделано
- Добавлен новый тип шаблона periodic_protocol в DocumentTemplate и init-команду; поддерживается fallback на media/document_templates/etalon/periodic_protocol_template.docx.
- Реализован генератор generate_periodic_protocol (docxtpl + динамическое добавление строк таблицы). Номер и дата протокола оставлены пустыми по требованию.
- Добавлена страница documents/periodic-protocol/ (см. PeriodicProtocolView), показывающая сотрудников с стажировкой или флагом «Ответственный за ОТ» с учетом прав доступа (AccessControlHelper). Есть чекбоксы и кнопки: скачать общий протокол или zip по подразделениям (пустое подразделение идет в общий).
- Верстка страницы: directory/templates/directory/documents/periodic_protocol.html, адаптивная таблица, счетчик выбранных, select-all.
- Импорты для комиссий берутся из directory.utils (по существующей логике ind_appropriate_commission).

## Плейсхолдеры и заполнение
- Используются плейсхолдеры из periodic_protocol_template.docx (io_nominative, position_nominative, 	icket_number, inding_name_genitive, chairman_name/position, secretary_name/position, и др.).
- Таблица заполняется в коде: строки добавляются программно для каждого выбранного сотрудника; поле «Вид проверки» заполняется значением «периодическая», номер билета — порядковый.

## Ограничения доступа и выбор сотрудников
- Базовый queryset фильтруется через AccessControlHelper.filter_queryset.
- В список попадают сотрудники, у которых position.internship_period_days > 0 или position.is_responsible_for_safety == True.
- Пустое подразделение/отдел попадает в общий протокол.

## Скачивание
- Общий протокол: один DOCX без сохранения в БД.
- По подразделениям: zip, файлы именуются periodic_protocol_<subdivision>.docx; если подразделение отсутствует — periodic_protocol_obshchiy.docx.

## Что осталось
- При необходимости добавить кастомизацию шаблона: заменить таблицу в DOCX на цикл не требуется, строки добавляются кодом.
- Проверить права/данные комиссий по существующей логике ind_appropriate_commission.
