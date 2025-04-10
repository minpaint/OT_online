# directory/utils/docx_generator.py
"""
📄 Утилиты для работы с DOCX (Анализ шаблонов)

Этот модуль теперь содержит вспомогательные функции, например, для анализа шаблонов.
Основная логика генерации перенесена в `directory/document_generators/`.
"""
import os
import logging
import re
from django.conf import settings
from directory.models.document_template import DocumentTemplate

# Настройка логирования
logger = logging.getLogger(__name__)


def analyze_template(template_id):
    """
    Анализ переменных, используемых в шаблоне документа.
    Полезно для отладки проблем с шаблонами.
    Args:
        template_id: ID шаблона для анализа
    """
    try:
        template = DocumentTemplate.objects.get(id=template_id)
        # Путь к файлу шаблона в медиа
        template_path = template.template_file.path

        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не найден: {template_path}")
            return {}

        # Используем python-docx для чтения текста
        from docx import Document
        doc = Document(template_path)
        content = ""
        for para in doc.paragraphs:
            content += para.text + ""

        # TODO: Улучшить извлечение переменных из таблиц и других элементов
        # Простой поиск переменных вида {{ variable_name }}
        variables = set(re.findall(r'{{[\s]*([^}]+)[\s]*}}', content))
        
        variables_info = {var.strip(): "Найден в тексте параграфов" for var in variables}

        logger.info(f"Найденные переменные в шаблоне '{template.name}' (ID: {template_id}):")
        for var, source in variables_info.items():
            logger.info(f"- {var} ({source})")
            
        return variables_info

    except DocumentTemplate.DoesNotExist:
        logger.error(f"Шаблон с ID {template_id} не найден.")
        return {}
    except ImportError:
        logger.error("Библиотека python-docx не установлена. Установите ее: pip install python-docx")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при анализе шаблона ID {template_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

# Функции get_document_template, prepare_employee_context, generate_docx_from_template
# и специфичные generate_* перенесены в directory/document_generators/
