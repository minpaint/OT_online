import os
from pathlib import Path


def create_file(path, description=""):
    """Создает файл с базовым комментарием, если файл не существует"""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            if description:
                f.write(f"# {description}\n# Заполните этот файл соответствующим кодом\n\n")
        print(f"Создан файл: {path}")
    else:
        print(f"Файл уже существует: {path}")


def create_template_file(path, description=""):
    """Создает файл шаблона с комментарием"""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            if description:
                f.write(f"<!-- {description} -->\n<!-- Заполните этот файл соответствующим HTML-кодом -->\n\n")
        print(f"Создан файл шаблона: {path}")
    else:
        print(f"Файл шаблона уже существует: {path}")


def main():
    # Базовый путь к проекту
    base_path = "D:/YandexDisk/OT_online"

    # 1. Модели
    create_file(
        os.path.join(base_path, "directory/models/commission.py"),
        "Модели для комиссий по проверке знаний"
    )

    # 2. Миграция (просто создаем директорию, миграцию создаст Django)
    migration_dir = os.path.join(base_path, "directory/migrations")
    if not os.path.exists(migration_dir):
        os.makedirs(migration_dir)
        print(f"Создана директория для миграций: {migration_dir}")

    # 3. Утилиты для работы с комиссиями
    create_file(
        os.path.join(base_path, "directory/utils/commission_service.py"),
        "Утилиты для работы с комиссиями"
    )

    # 4. Создание форм
    create_file(
        os.path.join(base_path, "directory/forms/commission.py"),
        "Формы для работы с комиссиями"
    )

    # 5. Представления
    create_file(
        os.path.join(base_path, "directory/views/commissions.py"),
        "Представления для работы с комиссиями"
    )
    create_file(
        os.path.join(base_path, "directory/views/documents/protocol.py"),
        "Представление для создания протокола проверки знаний с автоматическим выбором комиссии"
    )

    # 6. Административный интерфейс
    create_file(
        os.path.join(base_path, "directory/admin/commission_admin.py"),
        "Административный интерфейс для комиссий"
    )

    # 7. Шаблоны
    # Шаблоны для комиссий
    templates_dir = os.path.join(base_path, "templates/directory/commissions")
    os.makedirs(templates_dir, exist_ok=True)

    create_template_file(
        os.path.join(templates_dir, "list.html"),
        "Шаблон списка комиссий"
    )
    create_template_file(
        os.path.join(templates_dir, "detail.html"),
        "Шаблон детальной информации о комиссии"
    )
    create_template_file(
        os.path.join(templates_dir, "form.html"),
        "Шаблон формы для создания/редактирования комиссии"
    )
    create_template_file(
        os.path.join(templates_dir, "confirm_delete.html"),
        "Шаблон подтверждения удаления комиссии"
    )
    create_template_file(
        os.path.join(templates_dir, "member_form.html"),
        "Шаблон формы для добавления/редактирования участника комиссии"
    )
    create_template_file(
        os.path.join(templates_dir, "member_confirm_delete.html"),
        "Шаблон подтверждения удаления участника комиссии"
    )

    # Шаблон формы протокола
    create_template_file(
        os.path.join(base_path, "templates/directory/documents/protocol_form.html"),
        "Шаблон формы протокола проверки знаний с автоматическим выбором комиссии"
    )

    # 8. URLs - просто создаем заметку о необходимости обновить urls.py
    create_file(
        os.path.join(base_path, "notes_commission_urls.txt"),
        "ЗАМЕТКА: Необходимо добавить следующие URL-шаблоны в directory/urls.py:\n"
        "1. Добавить маршруты для комиссий\n"
        "2. Добавить маршрут для страницы создания протокола с авто-выбором комиссии\n"
        "Смотрите предоставленный код для urls.py в документации"
    )

    # 9. Генератор протоколов - заметка о необходимости обновить
    create_file(
        os.path.join(base_path, "notes_protocol_generator.txt"),
        "ЗАМЕТКА: Необходимо обновить файл directory/document_generators/protocol_generator.py\n"
        "для работы с автоматическим выбором комиссии"
    )

    print("\nВсе файлы успешно созданы. Теперь вы можете заполнить их соответствующим кодом.")
    print("Не забудьте обновить файлы urls.py и __init__.py для новых импортов.")


if __name__ == "__main__":
    main()