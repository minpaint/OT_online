#!/usr/bin/env python
"""
📁 Скрипт для создания структуры файлов для модуля документов

Этот скрипт создает необходимую структуру файлов и папок для реорганизации
представлений документов в проекте directory. Он проверяет существование
каждого файла и папки, и создает их, если они не существуют.

Использование:
    python create_documents_structure.py

Автор: ChatGPT
Дата: 2025-03-29
"""
import os
import sys


def create_directory(path):
    """Создает директорию, если она не существует."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"✅ Создана директория: {path}")
        except Exception as e:
            print(f"❌ Ошибка при создании директории {path}: {e}")
            return False
    else:
        print(f"ℹ️ Директория уже существует: {path}")
    return True


def create_file(path, content=""):
    """Создает файл с указанным содержимым, если он не существует."""
    if not os.path.exists(path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Создан файл: {path}")
        except Exception as e:
            print(f"❌ Ошибка при создании файла {path}: {e}")
            return False
    else:
        print(f"ℹ️ Файл уже существует: {path}")
    return True


def create_documents_structure():
    """Создает структуру файлов для модуля документов."""
    # Проверяем текущую директорию
    if not os.path.exists('directory'):
        print("❌ Ошибка: Директория 'directory' не найдена")
        print("⚠️ Запустите скрипт из корневой директории проекта")
        return False

    # Создаем основные директории
    directories = [
        'directory/views/documents',
    ]
    for directory in directories:
        if not create_directory(directory):
            return False

    # Создаем файлы с базовыми шаблонами
    files = [
        {
            'path': 'directory/views/documents/__init__.py',
            'content': '''"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует все представления для работы с документами,
чтобы их можно было импортировать из directory.views.documents
"""
# Импортировать представления после их создания
'''
        },
        {
            'path': 'directory/views/documents/selection.py',
            'content': '''"""
🔍 Представления для выбора типов документов

Содержит представления для выбора типов документов, которые нужно сгенерировать.
"""
# Реализация представлений выбора типов документов
'''
        },
        {
            'path': 'directory/views/documents/forms.py',
            'content': '''"""
📝 Представления для форм создания документов

Содержит представления для форм создания различных типов документов.
"""
# Реализация представлений форм создания документов
'''
        },
        {
            'path': 'directory/views/documents/preview.py',
            'content': '''"""
👁️ Представления для предпросмотра документов

Содержит представления для предпросмотра и редактирования документов перед генерацией.
"""
# Реализация представлений предпросмотра
'''
        },
        {
            'path': 'directory/views/documents/management.py',
            'content': '''"""
📊 Представления для управления сгенерированными документами

Содержит представления для просмотра списка документов, 
деталей документа и скачивания документов.
"""
# Реализация представлений управления документами
'''
        },
        {
            'path': 'directory/views/documents/utils.py',
            'content': '''"""
🔧 Вспомогательные функции для работы с документами

Содержит утилиты и вспомогательные функции для работы с документами.
"""
# Реализация вспомогательных функций
'''
        },
    ]

    for file_info in files:
        if not create_file(file_info['path'], file_info['content']):
            return False

    print("\n✅ Структура файлов успешно создана!")
    print("\nТеперь вы можете наполнить созданные файлы кодом из оригинального файла documents.py")
    print("Следуйте плану реорганизации, который был предложен ранее.")

    return True


if __name__ == "__main__":
    create_documents_structure()