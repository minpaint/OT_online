#!/usr/bin/env python3
"""
Скрипт для создания необходимых файлов для древовидного представления комиссий.
Запускайте скрипт из корневой директории проекта.
"""

import os
import sys


def create_directory(dir_path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            print(f"Директория {dir_path} успешно создана.")
        except OSError as e:
            print(f"Ошибка при создании директории {dir_path}: {e}")
            return False
    else:
        print(f"Директория {dir_path} уже существует.")
    return True


def create_file_if_not_exists(file_path):
    """Создает пустой файл, если он не существует"""
    if not os.path.exists(file_path):
        try:
            # Создаем директорию для файла, если она не существует
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Создаем пустой файл
            with open(file_path, 'w') as f:
                pass
            print(f"Файл {file_path} успешно создан.")
        except OSError as e:
            print(f"Ошибка при создании файла {file_path}: {e}")
            return False
    else:
        print(f"Файл {file_path} уже существует, пропускаем.")
    return True


def main():
    """Основная функция скрипта"""
    # Проверяем, что скрипт запущен из корневой директории проекта
    if not os.path.exists('directory'):
        print("Ошибка: Директория 'directory' не найдена!")
        print("Убедитесь, что вы запускаете скрипт из корневого каталога проекта.")
        return 1

    print("Создание необходимых директорий...")

    # Создаем директории
    directories = [
        'directory/views',
        'directory/templates/directory/commissions'
    ]

    for directory in directories:
        if not create_directory(directory):
            return 1

    print("Создание необходимых файлов...")

    # Создаем файлы
    files = [
        'directory/views/commission_tree.py',
        'directory/templates/directory/commissions/tree_view.html'
    ]

    for file_path in files:
        if not create_file_if_not_exists(file_path):
            return 1

    print("\nВсе необходимые файлы созданы или уже существуют.")
    print("Теперь вы можете заполнить их соответствующим кодом.")

    return 0


if __name__ == "__main__":
    sys.exit(main())