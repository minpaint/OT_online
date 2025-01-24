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
    tree_str = "СТРУКТУРА ФАЙЛОВ И ПАПОК\n"
    tree_str += "=" * 50 + "\n"
    root_name = os.path.basename(root_dir)
    tree_str += f"└── {root_name}\n"

    for root, dirs, files in os.walk(root_dir):
        depth = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * depth
        sub_indent = '    ' * (depth + 1)

        # Сортируем директории и файлы для лучшего порядка
        for dirname in sorted(dirs):
            tree_str += f"{indent}├── {dirname}\n"
        for filename in sorted(files):
            file_path = os.path.join(root, filename)
            formatted_size = get_formatted_size(file_path)
            tree_str += f"{indent}├── {filename} ({formatted_size})\n"
    return tree_str

def read_and_print_files():
    # Корневая директория проекта
    project_root = "D:/YandexDisk/OT_online"

    # Структура файлов для анализа
    files_to_analyze = {
        'Models': [
            'core/models/organizational_unit.py', # Добавлен organizational_unit.py
            'core/models/hierarchy.py',          # Проверяем hierarchy.py
            'core/models/organization.py',
            'core/models/department.py',
            'core/models/division.py',
            'core/models/position.py',
            'core/models/employee.py',
            'core/models/document.py',
            'core/models/__init__.py'
        ],
        'Forms': [
            'core/forms.py'
        ],
        'Views': [
            'core/views.py',
            'core/api/views.py'
        ],
        'URLs': [
            'core/urls.py',
            'core/api/urls.py'
        ],
        'Services': [
            'core/services/document_service.py',
            'core/services/employee_service.py',
            'core/services/organization_service.py'
        ],
        'Signals': [
            'core/signals/__init__.py'
        ],
        'Static JS': [
            'core/static/js/dependent_dropdowns.js',
            'core/static/admin/js/dependent_dropdowns.js'
        ],
        'Templates': [
            'core/templates/core/organization_form.html',
            'core/templates/core/position_form.html'
        ],
        'Admin Files': [ # Новая категория для admin.py
            'core/admin.py'
        ]
    }

    # Выводим структуру дерева директорий
    print(get_directory_tree(project_root))

    for category, files in files_to_analyze.items():
        print(f"\n{'=' * 80}\n{category}\n{'=' * 80}")

        for file_path in files:
            full_path = os.path.join(project_root, file_path)

            try:
                if os.path.exists(full_path):
                    print(f"\n--- {file_path} ---\n")
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(content)
                else:
                    print(f"\nFile not found: {file_path}")
            except Exception as e:
                print(f"\nError reading {file_path}: {str(e)}")


if __name__ == "__main__":
    read_and_print_files()