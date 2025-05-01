# directory/document_generators/siz_card_docx_generator.py
"""
🛡️ Генератор личной карточки учёта СИЗ (DOCX).

- Использует механизм маркеров аналогичный листу ознакомления
- Поддерживает объединенные строки для условий на лицевой стороне
- Заполняет только необходимые колонки на оборотной стороне
"""

import logging
import traceback
import re
from typing import Dict, Any, Optional, List

from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template,
    prepare_employee_context,
    generate_docx_from_template,
)
from directory.models.siz import SIZNorm
from directory.models.siz_issued import SIZIssued

logger = logging.getLogger(__name__)


# =============================================
# Основная функция генерации карточки СИЗ
# =============================================

def generate_siz_card_docx(
        employee,
        user=None,
        custom_context: Optional[Dict[str, Any]] = None,
) -> Optional[GeneratedDocument]:
    """Генерирует карточку учёта СИЗ для сотрудника."""

    try:
        # 1. Получение шаблона
        template = get_document_template("siz_card", employee)
        if not template:
            raise ValueError("Активный шаблон для карточки СИЗ не найден")

        # 2. Подготовка базового контекста
        context = prepare_employee_context(employee)
        full_name = context.get("fio_nominative", "")

        # 3. Определение пола для заголовка
        gender = _gender_from_patronymic(full_name)

        # 4. Получение выбранных норм СИЗ
        selected_norm_ids = []
        if custom_context:
            if 'selected_norm_ids' in custom_context:
                selected_norm_ids = custom_context['selected_norm_ids']
            elif 'selected_norms' in custom_context:
                selected_norm_ids = custom_context['selected_norms']

        # 5. Если нормы не выбраны, включаем все нормы для должности
        if not selected_norm_ids and hasattr(employee, 'position') and employee.position:
            logger.info("Нормы не выбраны, используем все нормы для должности")
            selected_norm_ids = list(SIZNorm.objects.filter(
                position=employee.position
            ).values_list('id', flat=True))

        # 6. Получение данных норм СИЗ
        norms_data = []
        if employee.position and selected_norm_ids:
            norm_query = SIZNorm.objects.filter(
                id__in=selected_norm_ids
            ).select_related('siz')

            for norm in norm_query:
                norms_data.append({
                    "name": norm.siz.name,
                    "classification": norm.siz.classification,
                    "unit": norm.siz.unit,
                    "quantity": norm.quantity,
                    "wear_period": "До износа" if norm.siz.wear_period == 0 else str(norm.siz.wear_period),
                    "condition": norm.condition  # Добавляем условие для группировки
                })

            logger.info(f"Найдено {len(norms_data)} норм СИЗ для сотрудника")

        # 7. Формирование контекста
        context.update({
            "card_number": f"SIZ-{employee.id}",
            "employee_full_name": full_name,
            "employee_gender": gender,
            "employee_height": getattr(employee, "height", "") or "",
            "employee_clothing_size": getattr(employee, "clothing_size", "") or "",
            "employee_shoe_size": getattr(employee, "shoe_size", "") or "",
            "department_name": context.get("department", ""),
            "position_name": context.get("position_nominative", ""),
            "hire_date": employee.hire_date.strftime("%d.%m.%Y") if hasattr(employee,
                                                                            "hire_date") and employee.hire_date else "",

            # Маркеры для таблиц
            "NORMS_TABLE": "NORMS_TABLE_MARKER",
            "ISSUED_TABLE": "ISSUED_TABLE_MARKER",

            # Данные для таблиц
            "siz_norms": norms_data,
            "issued_siz": norms_data  # Используем те же данные для оборотной стороны
        })

        # 8. Добавление пользовательского контекста
        if custom_context:
            for k, v in custom_context.items():
                if k not in ['selected_norm_ids', 'selected_norms']:
                    context[k] = v

        # 9. Генерация документа + пост-обработка
        return generate_docx_from_template(
            template,
            context,
            employee,
            user,
            post_processor=process_siz_card_tables,
        )

    except Exception as exc:
        logger.error("Ошибка при генерации карточки СИЗ: %s", exc)
        logger.error(traceback.format_exc())
        return None


# =========================
#   ПОСТ-ОБРАБОТКА ТАБЛИЦ
# =========================

def process_siz_card_tables(doc, context):
    """Обрабатывает таблицы в сгенерированном документе."""
    try:
        # Получаем данные норм СИЗ
        norms_data = context.get("siz_norms", [])
        if not norms_data:
            logger.warning("Нет данных о нормах СИЗ для обработки таблиц")
            return doc

        docx_document = doc.docx

        # Обрабатываем лицевую сторону
        processed_front = False
        for table in docx_document.tables:
            row_idx, cell_idx = _find_marker_in_table(table, "NORMS_TABLE_MARKER")
            if row_idx is not None:
                # Обработка таблицы лицевой стороны
                process_front_table(table, row_idx, cell_idx, norms_data)
                processed_front = True
                break

        if not processed_front:
            logger.warning("Маркер NORMS_TABLE_MARKER не найден в таблицах")

        # Обрабатываем оборотную сторону
        processed_back = False
        for table in docx_document.tables:
            row_idx, cell_idx = _find_marker_in_table(table, "ISSUED_TABLE_MARKER")
            if row_idx is not None:
                # Обработка таблицы оборотной стороны
                process_back_table(table, row_idx, cell_idx, norms_data)
                processed_back = True
                break

        if not processed_back:
            logger.warning("Маркер ISSUED_TABLE_MARKER не найден в таблицах")

        return doc

    except Exception as exc:
        logger.error("Ошибка при пост-обработке таблиц: %s", exc)
        logger.error(traceback.format_exc())
        return doc


def process_front_table(table, row_idx, cell_idx, norms_data):
    """Обрабатывает таблицу на лицевой стороне с объединёнными строками для условий."""
    try:
        # Группируем нормы по условиям
        grouped_norms = {}
        for norm in norms_data:
            condition = norm.get("condition", "")
            if condition not in grouped_norms:
                grouped_norms[condition] = []
            grouped_norms[condition].append(norm)

        # Удаляем маркер из ячейки
        cell = table.rows[row_idx].cells[cell_idx]
        cell.text = ""

        # Заполняем первую строку, если есть нормы без условий
        current_row = row_idx
        if "" in grouped_norms and grouped_norms[""]:
            for norm in grouped_norms[""]:
                if current_row >= len(table.rows):
                    new_row = table.add_row()
                else:
                    new_row = table.rows[current_row]

                _fill_front_row(new_row, norm)
                current_row += 1

        # Добавляем строки с условиями и соответствующими нормами
        for condition, norms in grouped_norms.items():
            if not condition:
                continue  # Пропускаем пустые условия, они уже обработаны

            # Добавляем строку с условием
            if current_row >= len(table.rows):
                condition_row = table.add_row()
            else:
                condition_row = table.rows[current_row]

            # Объединяем ячейки в строке условия
            first_cell = condition_row.cells[0]
            for i in range(1, len(condition_row.cells)):
                if i < len(condition_row.cells):
                    first_cell.merge(condition_row.cells[i])

            # Заполняем текст условия
            first_cell.text = condition
            for paragraph in first_cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.italic = True

            current_row += 1

            # Добавляем нормы для данного условия
            for norm in norms:
                if current_row >= len(table.rows):
                    new_row = table.add_row()
                else:
                    new_row = table.rows[current_row]

                _fill_front_row(new_row, norm)
                current_row += 1

        # Применяем форматирование ко всей таблице
        _apply_table_format(table)

    except Exception as e:
        logger.error(f"Ошибка при обработке таблицы лицевой стороны: {str(e)}")
        logger.error(traceback.format_exc())


def process_back_table(table, row_idx, cell_idx, norms_data):
    """Обрабатывает таблицу на оборотной стороне, заполняя только нужные колонки."""
    try:
        # Удаляем маркер из ячейки
        cell = table.rows[row_idx].cells[cell_idx]
        cell.text = ""

        # Определяем колонки для заполнения (0-based): 0, 1, 3, 6
        cols_to_fill = [0, 1, 3, 6]

        # Заполняем строки данными
        current_row = row_idx
        for norm in norms_data:
            if current_row >= len(table.rows):
                new_row = table.add_row()
            else:
                new_row = table.rows[current_row]

            # Заполняем только нужные колонки
            if 0 < len(new_row.cells):
                new_row.cells[0].text = norm.get("name", "")

            if 1 < len(new_row.cells):
                new_row.cells[1].text = norm.get("classification", "")

            if 3 < len(new_row.cells):
                new_row.cells[3].text = str(norm.get("quantity", ""))

            if 6 < len(new_row.cells):
                new_row.cells[6].text = "✓"  # Галочка в колонке расписки

            # Форматируем ячейки
            for col in cols_to_fill:
                if col < len(new_row.cells):
                    for paragraph in new_row.cells[col].paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    _set_cell_border(new_row.cells[col])

            current_row += 1

        # Применяем форматирование ко всей таблице
        _apply_table_format(table)

    except Exception as e:
        logger.error(f"Ошибка при обработке таблицы оборотной стороны: {str(e)}")
        logger.error(traceback.format_exc())


# --------------------------
#   УТИЛИТЫ
# --------------------------

def _gender_from_patronymic(full_name: str) -> str:
    """Определяет пол по отчеству."""
    parts = full_name.split()
    if len(parts) >= 3:
        patronymic = parts[2]
        if patronymic.endswith(("на", "вна", "чна", "кызы", "зы")):
            return "Женский"
        if patronymic.endswith(("ич", "ыч", "оглы", "улы", "лы")):
            return "Мужской"

    # По умолчанию считаем мужским
    return "Мужской"


def _find_marker_in_table(table, marker):
    """Находит маркер в таблице и возвращает координаты ячейки."""
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            for paragraph in cell.paragraphs:
                if marker in paragraph.text:
                    return r_idx, c_idx
    return None, None


def _fill_front_row(row, norm):
    """Заполняет строку таблицы на лицевой стороне."""
    # Проверяем наличие достаточного количества ячеек
    if len(row.cells) < 5:
        logger.warning(f"Недостаточно ячеек в строке таблицы: {len(row.cells)}")
        return

    # Заполняем ячейки
    row.cells[0].text = norm.get("name", "")
    row.cells[1].text = norm.get("classification", "")
    row.cells[2].text = norm.get("unit", "")
    row.cells[3].text = str(norm.get("quantity", ""))
    row.cells[4].text = norm.get("wear_period", "")

    # Форматируем ячейки
    for i in range(5):
        for paragraph in row.cells[i].paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cell_border(row.cells[i])


def _apply_table_format(table):
    """Применяет форматирование к таблице."""
    # 1. Попытка применить готовый стиль
    try:
        table.style = "Table Grid"
    except (KeyError, ValueError):
        logger.info("Стиль 'Table Grid' недоступен – проставляем границы вручную")
        _add_borders_manually(table)

    # 2. Шрифт всем run‑ам
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                if not para.runs:
                    para.add_run("")
                for run in para.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)


def _add_borders_manually(table):
    """Добавляет границы всем ячейкам таблицы."""
    for row in table.rows:
        for cell in row.cells:
            _set_cell_border(cell)


def _set_cell_border(
        cell,
        **kwargs,
):
    """Устанавливает одинарную границу толщиной 4 εм (≈0.5 pt) вокруг ячейки."""
    # Значения по умолчанию – все стороны single 4 εм
    sides = {
        "top": {
            "val": "single",
            "sz": "4",
            "color": "000000",
            "space": "0",
        },
        "left": {
            "val": "single",
            "sz": "4",
            "color": "000000",
            "space": "0",
        },
        "bottom": {
            "val": "single",
            "sz": "4",
            "color": "000000",
            "space": "0",
        },
        "right": {
            "val": "single",
            "sz": "4",
            "color": "000000",
            "space": "0",
        },
    }
    sides.update(kwargs)

    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    tblBorders = tcPr.find(qn("w:tcBorders"))
    if tblBorders is None:
        tblBorders = OxmlElement("w:tcBorders")
        tcPr.append(tblBorders)

    for edge in ("left", "top", "right", "bottom"):
        edge_el = tblBorders.find(qn(f"w:{edge}"))
        if edge_el is None:
            edge_el = OxmlElement(f"w:{edge}")
            tblBorders.append(edge_el)
        attrs = sides.get(edge, {})
        for key in ["val", "sz", "color", "space"]:
            edge_el.set(qn(f"w:{key}"), attrs.get(key, "single" if key == "val" else "4"))