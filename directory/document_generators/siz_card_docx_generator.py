# directory/document_generators/siz_card_docx_generator.py
"""
🛡️ Генератор карточки учета СИЗ в DOCX формате

Модуль реализует функции для создания личной карточки
учета средств индивидуальной защиты в формате DOCX,
используя подход аналогичный генератору листа ознакомления.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template,
    prepare_employee_context,
    generate_docx_from_template,
)
from directory.models.siz import SIZNorm, SIZIssued

logger = logging.getLogger(__name__)


def generate_siz_card_docx(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[
    GeneratedDocument]:
    """
    Генерирует карточку учета СИЗ в формате DOCX.

    Args:
        employee: Объект сотрудника
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст с доп. параметрами (опционально)
                        Может содержать selected_norm_ids для фильтрации норм СИЗ

    Returns:
        Optional[GeneratedDocument]: Созданный документ или None при ошибке
    """
    try:
        # 1. Загрузка шаблона
        template = get_document_template("siz_card_docx", employee)
        if not template:
            logger.error("Активный шаблон для карточки учета СИЗ не найден")
            raise ValueError("Активный шаблон для карточки учета СИЗ не найден")

        # 2. Подготовка базового контекста
        context = prepare_employee_context(employee)

        # 3. Добавление данных о нормах СИЗ
        # Проверяем, есть ли выбранные нормы СИЗ в пользовательском контексте
        selected_norm_ids = custom_context.get('selected_norm_ids', []) if custom_context else []

        norms_data = []
        if employee.position:
            # Базовый запрос для норм СИЗ
            norm_query = SIZNorm.objects.filter(position=employee.position).select_related('siz')

            # Если есть выбранные нормы, фильтруем по ним
            if selected_norm_ids:
                norm_query = norm_query.filter(id__in=selected_norm_ids)

            # Получаем отфильтрованные нормы
            siz_norms = norm_query

            for norm in siz_norms:
                norms_data.append({
                    'name': norm.siz.name,
                    'classification': norm.siz.classification,
                    'unit': norm.siz.unit,
                    'quantity': norm.quantity,
                    'wear_period': "До износа" if norm.siz.wear_period == 0 else f"{norm.siz.wear_period} мес."
                })

            logger.info(f"Получено {len(norms_data)} норм СИЗ для карточки")

        # 4. Добавление данных о выданных СИЗ
        issued_data = []
        siz_issued = SIZIssued.objects.filter(employee=employee).select_related('siz')

        # Если есть выбранные нормы, фильтруем выданные СИЗ по ним
        if selected_norm_ids:
            # Получаем ID выбранных СИЗ
            selected_siz_ids = SIZNorm.objects.filter(
                id__in=selected_norm_ids
            ).values_list('siz_id', flat=True)

            # Фильтруем выданные СИЗ по этим ID
            siz_issued = siz_issued.filter(siz_id__in=selected_siz_ids)

        for issued in siz_issued:
            issued_data.append({
                'name': issued.siz.name,
                'classification': issued.siz.classification,
                'issue_date': issued.issue_date.strftime("%d.%m.%Y") if issued.issue_date else "",
                'quantity': issued.quantity,
                'wear_percentage': f"{issued.wear_percentage}%" if issued.wear_percentage is not None else "",
                'return_date': issued.return_date.strftime("%d.%m.%Y") if issued.return_date else "",
                'cost': str(issued.cost) if issued.cost else "",
                'is_returned': issued.is_returned
            })

        logger.info(f"Получено {len(issued_data)} записей о выданных СИЗ для карточки")

        # 5. Добавление заглушек для шаблона и служебных маркеров
        context.update({
            # Номер личной карточки
            'card_number': f"SIZ-{employee.id}",

            # Данные сотрудника (заглушки)
            'employee_full_name': employee.full_name_nominative,
            'employee_gender': "Мужской",  # Заглушка
            'employee_height': employee.height or "170-176 см",
            'employee_clothing_size': employee.clothing_size or "48-50",
            'employee_shoe_size': employee.shoe_size or "42",
            'employee_tab_number': f"T-{employee.id}",  # Заглушка для табельного номера

            # Подразделение и должность
            'department_name': employee.department.name if employee.department else
            (employee.subdivision.name if employee.subdivision else ""),
            'position_name': employee.position.position_name if employee.position else "",

            # Даты
            'hire_date': employee.hire_date.strftime("%d.%m.%Y") if hasattr(employee,
                                                                            'hire_date') and employee.hire_date else "",
            'position_change_date': "",  # Заглушка для даты изменения должности

            # Списки данных для таблиц
            'siz_norms': norms_data,
            'siz_issued': issued_data,

            # Маркеры для поиска таблиц при пост-обработке
            'NORMS_MARKER': 'DOCMARKER_NORMS',
            'ISSUED_MARKER': 'DOCMARKER_ISSUED'

            # Блок подписей оставляем без изменений,
            # не используем заглушки для подписей
        })

        # 6. Применение пользовательского контекста (если передан)
        if custom_context:
            context.update(custom_context)

        # 7. Генерация документа с пост-обработкой таблиц
        return generate_docx_from_template(
            template,
            context,
            employee,
            user,
            post_processor=process_siz_card_tables
        )

    except Exception as e:
        logger.error(f"Ошибка при генерации карточки учета СИЗ: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def process_siz_card_tables(doc, context):
    """
    Обрабатывает таблицы в карточке СИЗ:
    1. Находит таблицу норм СИЗ по маркеру DOCMARKER_NORMS
    2. Находит таблицу выданных СИЗ по маркеру DOCMARKER_ISSUED
    3. Заполняет таблицы данными из контекста

    Args:
        doc: Документ DocxTemplate
        context: Контекст с данными

    Returns:
        doc: Обработанный документ
    """
    try:
        docx_document = doc.docx
        norms_data = context.get('siz_norms', [])
        issued_data = context.get('siz_issued', [])

        # Обрабатываем таблицу норм СИЗ
        norms_table, norms_row_idx = _find_table_by_marker(docx_document, 'DOCMARKER_NORMS')
        if norms_table and norms_row_idx is not None:
            _process_norms_table(norms_table, norms_row_idx, norms_data)
        else:
            logger.warning("Не найдена таблица норм СИЗ с маркером DOCMARKER_NORMS")

        # Обрабатываем таблицу выданных СИЗ
        issued_table, issued_row_idx = _find_table_by_marker(docx_document, 'DOCMARKER_ISSUED')
        if issued_table and issued_row_idx is not None:
            _process_issued_table(issued_table, issued_row_idx, issued_data)
        else:
            logger.warning("Не найдена таблица выданных СИЗ с маркером DOCMARKER_ISSUED")

        return doc

    except Exception as e:
        logger.error(f"Ошибка при обработке таблиц карточки СИЗ: {str(e)}")
        logger.error(traceback.format_exc())
        return doc


def _find_table_by_marker(docx_document, marker):
    """
    Находит таблицу и строку в ней по текстовому маркеру.

    Args:
        docx_document: Документ docx
        marker: Текстовый маркер для поиска

    Returns:
        tuple: (найденная таблица, индекс строки с маркером) или (None, None)
    """
    for table in docx_document.tables:
        for row_idx, row in enumerate(table.rows):
            for cell in row.cells:
                if marker in cell.text:
                    return table, row_idx
    return None, None


def _process_norms_table(table, template_row_idx, norms_data):
    """
    Обрабатывает таблицу норм СИЗ.

    Args:
        table: Таблица для обработки
        template_row_idx: Индекс строки-шаблона
        norms_data: Данные норм СИЗ
    """
    # Очищаем маркер в шаблонной строке
    template_row = table.rows[template_row_idx]
    for cell in template_row.cells:
        cell.text = cell.text.replace('DOCMARKER_NORMS', '')

    # Если нет данных, выходим
    if not norms_data:
        return

    # Заполняем первую запись в шаблонной строке
    _fill_norm_row(template_row, norms_data[0])

    # Добавляем строки для остальных записей
    for norm in norms_data[1:]:
        new_row = table.add_row()
        _copy_row_format(template_row, new_row)
        _fill_norm_row(new_row, norm)


def _fill_norm_row(row, norm_data):
    """
    Заполняет строку таблицы норм данными.

    Args:
        row: Строка таблицы
        norm_data: Данные для заполнения
    """
    if len(row.cells) >= 5:  # Минимальное количество ячеек для норм СИЗ
        try:
            row.cells[0].text = norm_data.get('name', '')
            row.cells[1].text = norm_data.get('classification', '')
            row.cells[2].text = norm_data.get('unit', '')
            row.cells[3].text = str(norm_data.get('quantity', ''))
            row.cells[4].text = norm_data.get('wear_period', '')

            # Применение форматирования
            _apply_cell_formats(row)
        except Exception as e:
            logger.error(f"Ошибка при заполнении строки нормы СИЗ: {str(e)}")


def _process_issued_table(table, template_row_idx, issued_data):
    """
    Обрабатывает таблицу выданных СИЗ.

    Args:
        table: Таблица для обработки
        template_row_idx: Индекс строки-шаблона
        issued_data: Данные выданных СИЗ
    """
    # Очищаем маркер в шаблонной строке
    template_row = table.rows[template_row_idx]
    for cell in template_row.cells:
        cell.text = cell.text.replace('DOCMARKER_ISSUED', '')

    # Если нет данных, выходим
    if not issued_data:
        return

    # Заполняем первую запись в шаблонной строке
    _fill_issued_row(template_row, issued_data[0])

    # Добавляем строки для остальных записей
    for issued in issued_data[1:]:
        new_row = table.add_row()
        _copy_row_format(template_row, new_row)
        _fill_issued_row(new_row, issued)


def _fill_issued_row(row, issued_data):
    """
    Заполняет строку таблицы выданных СИЗ данными.

    Args:
        row: Строка таблицы
        issued_data: Данные выданного СИЗ
    """
    try:
        # Проверяем количество ячеек в строке
        cells_count = len(row.cells)
        if cells_count < 7:
            logger.warning(f"Недостаточно ячеек в строке таблицы выданных СИЗ: {cells_count}")
            return

        # Заполняем доступные ячейки
        row.cells[0].text = issued_data.get('name', '')
        row.cells[1].text = issued_data.get('classification', '')
        row.cells[2].text = issued_data.get('issue_date', '')
        row.cells[3].text = str(issued_data.get('quantity', ''))
        row.cells[4].text = issued_data.get('wear_percentage', '')

        if issued_data.get('is_returned') and cells_count >= 11:
            # Заполняем ячейки для возвращенных СИЗ
            row.cells[7].text = issued_data.get('return_date', '')
            row.cells[8].text = str(issued_data.get('quantity', ''))  # То же количество
            row.cells[9].text = issued_data.get('wear_percentage', '')  # То же значение износа
            row.cells[10].text = issued_data.get('cost', '')

        # Применение форматирования
        _apply_cell_formats(row)
    except Exception as e:
        logger.error(f"Ошибка при заполнении строки выданных СИЗ: {str(e)}")


def _copy_row_format(src_row, dst_row):
    """
    Копирует форматирование из одной строки в другую.

    Args:
        src_row: Исходная строка (шаблон)
        dst_row: Целевая строка
    """
    try:
        # Копируем высоту строки
        dst_row.height = src_row.height

        # Копируем стили ячеек, если количество ячеек совпадает
        for idx in range(min(len(src_row.cells), len(dst_row.cells))):
            src_cell = src_row.cells[idx]
            dst_cell = dst_row.cells[idx]

            # Применяем стили и границы
            _set_cell_border(dst_cell)

    except Exception as e:
        logger.error(f"Ошибка при копировании формата строки: {str(e)}")


def _apply_cell_formats(row):
    """
    Применяет форматирование ко всем ячейкам в строке.

    Args:
        row: Строка таблицы
    """
    for cell in row.cells:
        # Устанавливаем шрифт для всех параграфов в ячейке
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

        # Устанавливаем границы ячейки
        _set_cell_border(cell)


def _set_cell_border(cell):
    """
    Устанавливает одинарную границу для ячейки.

    Args:
        cell: Ячейка таблицы
    """
    # Значения по умолчанию - все стороны single 4 εм
    borders = {
        "top": {"val": "single", "sz": "4", "color": "000000"},
        "left": {"val": "single", "sz": "4", "color": "000000"},
        "bottom": {"val": "single", "sz": "4", "color": "000000"},
        "right": {"val": "single", "sz": "4", "color": "000000"},
    }

    # Применяем границы к ячейке
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    # Добавляем границы
    tcBorders = OxmlElement('w:tcBorders')
    tcPr.append(tcBorders)

    # Создаем каждую границу
    for edge, attrs in borders.items():
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), attrs['val'])
        border.set(qn('w:sz'), attrs['sz'])
        border.set(qn('w:color'), attrs['color'])
        border.set(qn('w:space'), "0")
        tcBorders.append(border)