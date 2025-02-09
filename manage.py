#!/usr/bin/env python
"""
🚀 Скрипт для запуска административных задач Django.
"""
import os
import sys
from pathlib import Path

def main():
    # Определяем корневой каталог проекта (D:\YandexDisk\OT_online)
    BASE_DIR = Path(__file__).resolve().parent
    # Добавляем BASE_DIR в PYTHONPATH
    sys.path.append(str(BASE_DIR))
    # Устанавливаем переменную окружения для настроек Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что Django установлен и доступен в PYTHONPATH."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
