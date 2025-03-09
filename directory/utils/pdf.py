# 📁 directory/utils/pdf.py

import os
import logging
from io import BytesIO
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings

# Настройка логирования
logger = logging.getLogger(__name__)


def render_to_pdf(template_path, context, filename=None, as_attachment=True):
    """
    🖨️ Функция для рендеринга HTML-шаблона в PDF-файл

    Args:
        template_path (str): Путь к HTML-шаблону
        context (dict): Контекст с данными для шаблона
        filename (str, optional): Имя файла для скачивания
        as_attachment (bool): Отправить как вложение (True) или отобразить в браузере (False)

    Returns:
        HttpResponse: HTTP-ответ с PDF-файлом или сообщением об ошибке
    """
    try:
        # Добавляем STATIC_URL в контекст, если его нет
        if 'STATIC_URL' not in context:
            context['STATIC_URL'] = settings.STATIC_URL

        # Рендеринг HTML-шаблона
        template = get_template(template_path)
        html_string = template.render(context)

        # Создание объекта BytesIO для записи PDF
        result = BytesIO()

        # Путь к шрифтам
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts')

        # Настройки PDF
        pdf_options = {
            'font_path': font_path,
            'default_font': 'DejaVuSans',
        }

        # Создание PDF
        pdf = pisa.CreatePDF(
            BytesIO(html_string.encode('UTF-8')),
            dest=result,
            **pdf_options
        )

        # Проверка на ошибки
        if pdf.err:
            logger.error(f"Ошибка при создании PDF: {pdf.err}")
            return HttpResponse(f"Ошибка при создании PDF: {pdf.err}", status=500)

        # Формирование HTTP-ответа
        response = HttpResponse(result.getvalue(), content_type='application/pdf')

        # Настройка заголовка Content-Disposition
        if filename:
            disposition = 'attachment' if as_attachment else 'inline'
            # Обеспечиваем корректное имя файла для разных браузеров
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'

        return response

    except Exception as e:
        logger.exception(f"Непредвиденная ошибка при создании PDF: {str(e)}")
        return HttpResponse(
            f"Произошла ошибка при создании PDF: {str(e)}",
            status=500
        )