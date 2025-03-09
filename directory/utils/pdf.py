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


def render_to_pdf(template_path, context, filename=None, as_attachment=True):
    """
    Функция для рендеринга HTML-шаблона в PDF-файл

    Args:
        template_path (str): Путь к HTML-шаблону
        context (dict): Контекст с данными для шаблона
        filename (str, optional): Имя файла для скачивания
        as_attachment (bool): Отправить как вложение (True) или отобразить в браузере (False)

    Returns:
        HttpResponse: HTTP-ответ с PDF-файлом или сообщением об ошибке
    """
    try:
        context['STATIC_URL'] = settings.STATIC_URL
        context['BASE_DIR'] = settings.BASE_DIR

        template = get_template(template_path)
        html_string = template.render(context)

        result = BytesIO()

        pdf = pisa.pisaDocument(
            BytesIO(html_string.encode('UTF-8')),
            dest=result,
            encoding='UTF-8',
            link_callback=fetch_resources
        )

        if pdf.err:
            logger.error(f"Ошибка при создании PDF: {pdf.err}")
            return HttpResponse(f"Ошибка при создании PDF: {pdf.err}", status=500)

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
