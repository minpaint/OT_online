# 📁 directory/utils/pdf.py

import os
import logging
from io import BytesIO
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Импорт для подмены шрифтов по умолчанию в xhtml2pdf
from xhtml2pdf.default import DEFAULT_FONT

# Настройка логирования
logger = logging.getLogger(__name__)

# 📌 Регистрируем шрифт DejaVuSans под именем "helvetica"
try:
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('helvetica', font_path))

    # Подменяем стандартные шрифты "helvetica" и "times" на наш DejaVuSans
    DEFAULT_FONT['helvetica'] = 'helvetica'
    DEFAULT_FONT['times'] = 'helvetica'

    logger.info("✅ Шрифт DejaVuSans успешно зарегистрирован как 'helvetica'")
except Exception as e:
    logger.error(f"❌ Ошибка регистрации шрифта: {e}")


def fetch_resources(uri, rel):
    """
    Функция для получения ресурсов (шрифтов, изображений) для PDF

    Args:
        uri: URI ресурса
        rel: Относительный путь

    Returns:
        Абсолютный путь к ресурсу
    """
    logger.debug(f"Запрошен ресурс: {uri}")

    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.BASE_DIR, 'static', uri.replace(settings.STATIC_URL, ""))
    elif uri.startswith('/static/'):
        path = os.path.join(settings.BASE_DIR, uri[1:])  # Убираем начальный слэш
    else:
        path = os.path.join(settings.BASE_DIR, 'static', uri)

    if os.path.exists(path):
        logger.debug(f"Найден ресурс: {path}")
        return path
    else:
        logger.warning(f"Ресурс не найден: {path}")
        return uri


def render_to_pdf(template_path, context, filename=None, as_attachment=True, landscape=False, pdf_options=None):
    """
    🖨️ Функция для рендеринга HTML-шаблона в PDF-файл

    Args:
        template_path (str): Путь к HTML-шаблону
        context (dict): Контекст с данными для шаблона
        filename (str, optional): Имя файла для скачивания
        as_attachment (bool): Отправить как вложение (True) или отобразить в браузере (False)
        landscape (bool): Ориентация страницы - альбомная (True) или книжная (False)
        pdf_options (dict, optional): Дополнительные опции для PDF генерации

    Returns:
        HttpResponse: HTTP-ответ с PDF-файлом или сообщением об ошибке
    """
    try:
        context['STATIC_URL'] = settings.STATIC_URL
        context['BASE_DIR'] = settings.BASE_DIR

        template = get_template(template_path)
        html_string = template.render(context)

        result = BytesIO()

        # Настройки для PDF
        options = {
            'encoding': 'UTF-8',
            'link_callback': fetch_resources
        }

        # Настройка ориентации страницы
        if landscape:
            # В xhtml2pdf можно задать ориентацию через CSS @page или через параметр
            # Используем параметр для совместимости
            options['page_size'] = 'A4-L'  # A4 в ландшафтной ориентации

        # Добавляем дополнительные опции, если они переданы
        if pdf_options:
            options.update(pdf_options)

        # 🔄 Улучшаем опции для отображения таблиц
        if 'table_header_font_name' not in options:
            options['table_header_font_name'] = 'helvetica'

        if 'table_header_font_size' not in options:
            options['table_header_font_size'] = 9

        # Добавляем опции для улучшения отображения таблиц
        options.setdefault('margin-top', '0.5cm')
        options.setdefault('margin-right', '0.5cm')
        options.setdefault('margin-bottom', '0.5cm')
        options.setdefault('margin-left', '0.5cm')

        # Установим низкий уровень логирования для pisa, чтобы видеть больше деталей
        import logging
        pisa_logger = logging.getLogger('xhtml2pdf')
        original_level = pisa_logger.level
        pisa_logger.setLevel(logging.DEBUG)

        logger.debug(f"📊 Генерация PDF с опциями: {options}")

        pdf = pisa.pisaDocument(
            BytesIO(html_string.encode('UTF-8')),
            dest=result,
            **options
        )

        # Возвращаем уровень логирования
        pisa_logger.setLevel(original_level)

        if pdf.err:
            errors = [f"Ошибка {i}: {err}" for i, err in enumerate(pdf.err) if err]
            error_msg = "\n".join(errors) if errors else str(pdf.err)
            logger.error(f"Ошибка при создании PDF: {error_msg}")
            return HttpResponse(f"Ошибка при создании PDF: {error_msg}", status=500)

        response = HttpResponse(result.getvalue(), content_type='application/pdf')

        if filename:
            disposition = 'attachment' if as_attachment else 'inline'
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'

        return response

    except Exception as e:
        logger.exception(f"Ошибка при создании PDF: {str(e)}")
        return HttpResponse(
            f"Произошла ошибка при создании PDF: {str(e)}",
            status=500
        )