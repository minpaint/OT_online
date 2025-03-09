# 📁 directory/utils/create_fonts_dir.py

import os
from django.conf import settings


def create_fonts_directory():
    """
    📁 Создает директорию для шрифтов, если она не существует
    """
    font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')

    if not os.path.exists(font_dir):
        try:
            os.makedirs(font_dir)
            print(f"✅ Создана директория для шрифтов: {font_dir}")

            # Проверка наличия DejaVuSans
            dejavu_font = os.path.join(font_dir, 'DejaVuSans.ttf')
            if not os.path.exists(dejavu_font):
                print(f"⚠️ Шрифт DejaVuSans.ttf не найден в {font_dir}")
                print("ℹ️ Пожалуйста, скачайте и установите шрифты DejaVu Sans:")
                print("   https://dejavu-fonts.github.io/")

        except Exception as e:
            print(f"❌ Ошибка при создании директории для шрифтов: {str(e)}")
    else:
        print(f"✓ Директория для шрифтов уже существует: {font_dir}")


if __name__ == "__main__":
    create_fonts_directory()