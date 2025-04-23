import os
import sys


def create_directory_structure(base_path):
    """
    Создает структуру каталогов и файлов для системы медосмотров

    Args:
        base_path: Базовый путь проекта
    """
    # Убедимся, что базовый путь существует
    if not os.path.exists(base_path):
        print(f"Ошибка: Базовый путь {base_path} не существует")
        return False

    # Проверяем основной каталог приложения
    app_dir = os.path.join(base_path, 'directory')
    if not os.path.exists(app_dir):
        print(f"Ошибка: Каталог приложения {app_dir} не существует")
        return False

    # Структура каталогов и файлов для создания
    structure = {
        'models': {
            '__init__.py': "# Импортируем модели медосмотров\nfrom .medical_examination import MedicalExaminationType, HarmfulFactor\nfrom .medical_norm import MedicalExaminationNorm, PositionMedicalExamination\n",
            'medical_examination.py': "",
            'medical_norm.py': "",
        },
        'admin': {
            '__init__.py': "# Импортируем админки медосмотров\nfrom .medical_examination import *\n",
            'medical_examination.py': "",
        },
        'forms': {
            '__init__.py': "# Импортируем формы для медосмотров\nfrom .medical_examination import *\n",
            'medical_examination.py': "",
        },
        'utils': {
            'medical_examination.py': "",
        },
        'views': {
            'medical_examination.py': "",
        },
        'templates/directory/medical_exams/medical_norms': {
            'import.html': "",
            'export.html': "",
            'list.html': "",
            'form.html': "",
            'confirm_delete.html': "",
        }
    }

    # Создаем файлы и каталоги
    files_created = 0
    directories_created = 0

    for dir_path, files in structure.items():
        full_dir_path = os.path.join(app_dir, dir_path)

        # Создаем каталог, если не существует
        if not os.path.exists(full_dir_path):
            try:
                os.makedirs(full_dir_path)
                print(f"Создан каталог: {full_dir_path}")
                directories_created += 1
            except Exception as e:
                print(f"Не удалось создать каталог {full_dir_path}: {str(e)}")
                continue

        # Создаем файлы в каталоге
        for file_name, content in files.items():
            full_file_path = os.path.join(full_dir_path, file_name)

            # Не перезаписываем существующие файлы
            if os.path.exists(full_file_path):
                print(f"Файл уже существует (пропускаем): {full_file_path}")
                continue

            try:
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Создан файл: {full_file_path}")
                files_created += 1
            except Exception as e:
                print(f"Не удалось создать файл {full_file_path}: {str(e)}")

    # Проверяем на существование и обновляем urls.py
    urls_path = os.path.join(app_dir, 'urls.py')
    if os.path.exists(urls_path):
        print(f"Файл {urls_path} существует. Добавьте в него URL-маршруты для медосмотров вручную.")

    print(f"\nИтого: создано {directories_created} каталогов и {files_created} файлов.")
    return True


if __name__ == "__main__":
    # Базовый путь проекта (можно передать аргументом)
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = r"D:\YandexDisk\OT_online"

    print(f"Создание структуры файлов для проекта медосмотров в {base_path}...")
    success = create_directory_structure(base_path)

    if success:
        print("\nСтруктура файлов успешно создана!")
        print("Теперь вы можете наполнить содержимым следующие файлы:")
        print("1. directory/models/medical_examination.py - модели для видов медосмотров и вредных факторов")
        print("2. directory/models/medical_norm.py - модели для эталонных норм и переопределений")
        print("3. directory/admin/medical_examination.py - админки")
        print("4. directory/forms/medical_examination.py - формы")
        print("5. directory/utils/medical_examination.py - утилиты импорта/экспорта")
        print("6. directory/views/medical_examination.py - представления")
    else:
        print("\nВозникли ошибки при создании структуры файлов.")