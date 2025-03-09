import os
import pdfkit
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from io import BytesIO
from directory.models import Employee, SIZIssued, SIZNorm, Position


@login_required
def export_personal_card_pdf(request, employee_id):
    """
    📄 Экспорт личной карточки учета СИЗ в формате PDF для печати на A4
    Использует wkhtmltopdf для генерации PDF с корректной поддержкой кириллицы

    Args:
        request: HttpRequest объект
        employee_id: ID сотрудника

    Returns:
        HttpResponse с PDF-документом
    """
    # Получаем объект сотрудника
    employee = get_object_or_404(Employee, id=employee_id)

    # Получаем данные для карточки
    issued_items = SIZIssued.objects.filter(
        employee=employee
    ).select_related('siz').order_by('-issue_date')

    # Данные о нормах СИЗ
    base_norms = []
    condition_groups = []

    if employee.position:
        # Получаем непосредственные нормы должности
        direct_norms = SIZNorm.objects.filter(
            position=employee.position
        ).select_related('siz')

        # Получаем эталонные нормы по названию должности
        reference_norms = Position.find_reference_norms(employee.position.position_name)

        # Формируем словарь норм, где ключ - комбинация siz_id + condition
        norm_dict = {}

        # Добавляем эталонные нормы
        for norm in reference_norms:
            key = f"{norm.siz_id}_{norm.condition}"
            norm_dict[key] = norm

        # Добавляем прямые нормы с более высоким приоритетом
        for norm in direct_norms:
            key = f"{norm.siz_id}_{norm.condition}"
            norm_dict[key] = norm

        # Группируем нормы по условиям
        condition_groups_dict = {}

        for key, norm in norm_dict.items():
            if not norm.condition:
                base_norms.append(norm)
            else:
                if norm.condition not in condition_groups_dict:
                    condition_groups_dict[norm.condition] = []
                condition_groups_dict[norm.condition].append(norm)

        # Сортируем нормы
        base_norms.sort(key=lambda x: (x.order, x.siz.name))

        condition_groups = [
            {'name': condition, 'norms': sorted(norms, key=lambda x: (x.order, x.siz.name))}
            for condition, norms in condition_groups_dict.items()
        ]

    # Подготавливаем контекст для шаблона
    context = {
        'employee': employee,
        'issued_items': issued_items,
        'base_norms': base_norms,
        'condition_groups': condition_groups,
        'title': f'Личная карточка учета СИЗ - {employee.full_name_nominative}',
        'is_pdf': True,  # Флаг для шаблона, что это PDF-версия
        'now': timezone.now(),  # Текущая дата и время для отображения в PDF
        'static_url': settings.STATIC_URL,  # URL для статических файлов
    }

    # Загружаем шаблон
    template = get_template('directory/siz_issued/personal_card_pdf.html')
    html_content = template.render(context)

    # Опции для wkhtmltopdf
    options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'margin-top': '1cm',
        'margin-right': '1cm',
        'margin-bottom': '1cm',
        'margin-left': '1cm',
        'title': context['title'],
    }

    # Используем путь к wkhtmltopdf из настроек или автоопределение
    if hasattr(settings, 'WKHTMLTOPDF_CMD') and settings.WKHTMLTOPDF_CMD:
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)
        pdf = pdfkit.from_string(html_content, False, options=options, configuration=config)
    else:
        # Проверяем операционную систему
        if os.name == 'nt':  # Windows
            # Укажите ваш путь к wkhtmltopdf.exe или добавьте его в PATH
            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            pdf = pdfkit.from_string(html_content, False, options=options, configuration=config)
        else:  # Linux/Unix
            pdf = pdfkit.from_string(html_content, False, options=options)

    # Формируем HTTP-ответ с PDF
    response = HttpResponse(pdf, content_type='application/pdf')

    # Транслитерация имени для использования в имени файла
    # Простая функция для транслитерации кириллицы
    def transliterate(name):
        # Словарь замен (можно расширить при необходимости)
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
            ' ': '_', '-': '_'
        }
        # Заменяем символы
        result = ""
        for char in name:
            result += translit_dict.get(char, char)
        return result

    # Формируем имя файла для скачивания
    transliterated_name = transliterate(employee.full_name_nominative)
    filename = f"siz_card_{employee.id}_{transliterated_name}.pdf"

    # Заголовок для скачивания файла
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response