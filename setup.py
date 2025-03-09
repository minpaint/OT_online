# 📁 check_fonts.py

import os
import sys
from django.conf import settings


def check_font_files():
    """
    Проверяет наличие шрифтов для xhtml2pdf
    """
    # Путь к директории шрифтов
    font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')

    # Список шрифтов для проверки
    fonts_to_check = [
        'DejaVuSans.ttf',
        'DejaVuSerif.ttf',
        'DejaVuSansMono.ttf'
    ]

    # Проверяем, существует ли директория
    if not os.path.exists(font_dir):
        print(f"❌ Директория шрифтов не найдена: {font_dir}")

        # Создаем директорию, если её нет
        try:
            os.makedirs(font_dir)
            print(f"✅ Создана директория для шрифтов: {font_dir}")
        except Exception as e:
            print(f"❌ Ошибка при создании директории: {str(e)}")
            return False
    else:
        print(f"✅ Директория шрифтов найдена: {font_dir}")

    # Проверяем каждый шрифт
    missing_fonts = []
    for font in fonts_to_check:
        font_path = os.path.join(font_dir, font)
        if os.path.exists(font_path):
            print(f"✅ Шрифт найден: {font}")
        else:
            print(f"❌ Шрифт не найден: {font}")
            missing_fonts.append(font)

    if missing_fonts:
        print("\n⚠️ Отсутствуют следующие шрифты:")
        for font in missing_fonts:
            print(f"  - {font}")

        print("\nПожалуйста, скачайте шрифты DejaVu с официального сайта:")
        print("https://dejavu-fonts.github.io/")
        print(f"и поместите их в директорию: {font_dir}")

        return False

    return True


if __name__ == "__main__":
    # Настройка Django
    import django

    django.setup()

    # Проверка шрифтов
    if check_font_files():
        print("\n✅ Все необходимые шрифты найдены и готовы к использованию.")
    else:
        print("\n⚠️ Необходимо установить отсутствующие шрифты.")