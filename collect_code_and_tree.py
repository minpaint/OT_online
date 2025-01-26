import os


def get_formatted_size(file_path):
    """Получает размер файла и форматирует его в удобочитаемом виде."""
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_directory_tree(root_dir):
    """Создает строковое представление дерева директорий и файлов."""
    # Только служебные директории и файлы для исключения
    excluded_dirs = {
        'venv',
        '__pycache__',
        '.git',
        '.idea'
    }

    excluded_files = {
        '.gitignore',
        'db.sqlite3',
        '.env',
        '*.pyc',
        '.DS_Store'
    }

    tree_str = "СТРУКТУРА ПРОЕКТА\n"
    tree_str += "=" * 50 + "\n"

    for root, dirs, files in os.walk(root_dir):
        # Исключаем только служебные директории
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        level = root.replace(root_dir, '').count(os.sep)
        indent = '│   ' * level

        if level > 0:
            tree_str += f"{indent[:-4]}├── {os.path.basename(root)}/\n"
        else:
            tree_str += f"└── {os.path.basename(root)}/\n"

        # Добавляем все файлы, кроме служебных
        for f in sorted(files):
            if any(f.endswith(excluded) for excluded in excluded_files):
                continue
            file_path = os.path.join(root, f)
            size = get_formatted_size(file_path)
            tree_str += f"{indent}├── {f} ({size})\n"

    return tree_str


def print_file_content(file_path, relative_path):
    """Печатает содержимое файла с форматированием."""
    try:
        print(f"\n{'=' * 80}")
        print(f"--- {relative_path} ---")
        print(f"{'=' * 80}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        print(f"\nРазмер файла: {get_formatted_size(file_path)}")
    except Exception as e:
        print(f"Ошибка при чтении файла {relative_path}: {str(e)}")


def read_all_project_files(project_root):
    """Читает и выводит структуру и содержимое всех файлов проекта, кроме служебных."""
    # Сначала выводим структуру проекта
    print(get_directory_tree(project_root))

    print("\nСОДЕРЖИМОЕ ФАЙЛОВ ПРОЕКТА:")
    print("=" * 50)

    # Служебные директории и файлы для исключения
    excluded_dirs = {
        'venv',
        '__pycache__',
        '.git',
        '.idea'
    }

    excluded_files = {
        '.gitignore',
        'db.sqlite3',
        '.env',
        '*.pyc',
        '.DS_Store'
    }

    # Собираем все файлы проекта
    for root, dirs, files in os.walk(project_root):
        # Пропускаем служебные директории
        if any(excluded in root for excluded in excluded_dirs):
            continue

        for file in sorted(files):
            # Пропускаем служебные файлы
            if any(file.endswith(excluded) for excluded in excluded_files):
                continue

            relative_path = os.path.relpath(os.path.join(root, file), project_root)
            file_path = os.path.join(root, file)
            print_file_content(file_path, relative_path)


if __name__ == "__main__":
    project_root = "D:/YandexDisk/OT_online"  # Укажите свой путь к проекту
    read_all_project_files(project_root)