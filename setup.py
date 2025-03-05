#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
📂 Скрипт для создания структуры файлов и директорий для функциональности учета СИЗ
"""

import os
import argparse
from datetime import datetime


def create_directory(path):
    """
    Создает директорию, если она не существует

    Args:
        path (str): Путь к директории
    """
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Создана директория: {path}")
    else:
        print(f"📂 Директория уже существует: {path}")


def create_empty_file(path):
    """
    Создает пустой файл, если файл не существует

    Args:
        path (str): Путь к файлу
    """
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            pass
        print(f"✅ Создан пустой файл: {path}")
    else:
        print(f"📄 Файл уже существует: {path}")


def create_init_file(directory_path):
    """
    Создает __init__.py файл в указанной директории

    Args:
        directory_path (str): Путь к директории
    """
    init_path = os.path.join(directory_path, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w', encoding='utf-8') as f:
            pass
        print(f"✅ Создан файл __init__.py в {directory_path}")
    else:
        print(f"📄 Файл __init__.py уже существует в {directory_path}")


def setup_directory_structure(base_dir):
    """
    Создает структуру директорий для функциональности учета СИЗ

    Args:
        base_dir (str): Базовая директория проекта
    """
    directory_app = os.path.join(base_dir, 'directory')

    # Создаем основные директории
    directories = [
        os.path.join(directory_app, 'models'),
        os.path.join(directory_app, 'views'),
        os.path.join(directory_app, 'forms'),
        os.path.join(directory_app, 'templates', 'directory', 'siz_issued'),
        os.path.join(directory_app, 'admin'),
        os.path.join(directory_app, 'migrations'),
    ]

    for directory in directories:
        create_directory(directory)
        create_init_file(directory)

    # Создаем пустые файлы для моделей
    model_files = [
        os.path.join(directory_app, 'models', 'siz_issued.py'),
    ]

    for file_path in model_files:
        create_empty_file(file_path)

    # Создаем пустые файлы для форм
    form_files = [
        os.path.join(directory_app, 'forms', 'siz_issued.py'),
    ]

    for file_path in form_files:
        create_empty_file(file_path)

    # Создаем пустые файлы для представлений
    view_files = [
        os.path.join(directory_app, 'views', 'siz_issued.py'),
    ]

    for file_path in view_files:
        create_empty_file(file_path)

    # Создаем пустые файлы для шаблонов
    template_files = [
        os.path.join(directory_app, 'templates', 'directory', 'siz_issued', 'issue_form.html'),
        os.path.join(directory_app, 'templates', 'directory', 'siz_issued', 'personal_card.html'),
        os.path.join(directory_app, 'templates', 'directory', 'siz_issued', 'return_form.html'),
    ]

    for file_path in template_files:
        create_empty_file(file_path)

    # Создаем пустой файл для админки
    admin_files = [
        os.path.join(directory_app, 'admin', 'siz_issued.py'),
    ]

    for file_path in admin_files:
        create_empty_file(file_path)

    # Создаем пустой файл для миграции
    current_time = datetime.now().strftime('%Y%m%d_%H%M')
    migration_file = os.path.join(directory_app, 'migrations', f'{current_time}_siz_issued.py')
    create_empty_file(migration_file)


def main():
    """
    Основная функция для запуска скрипта
    """
    parser = argparse.ArgumentParser(description='Скрипт для создания структуры файлов и директорий для учета СИЗ')
    parser.add_argument('--base-dir', type=str, default='.',
                        help='Базовая директория проекта (по умолчанию: текущая директория)')

    args = parser.parse_args()

    print("🚀 Запуск скрипта создания структуры для функциональности учета СИЗ...")
    setup_directory_structure(args.base_dir)
    print("✅ Создание структуры завершено! Теперь вы можете наполнить файлы кодом.")


if __name__ == "__main__":
    main()