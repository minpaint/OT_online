import os

# Константы для исключения служебных файлов и директорий Django
EXCLUDE_DIRS = {
    'venv',
    '.venv',
    '__pycache__',
    '.git',
    '.idea',
    'node_modules',
    'dist',
    'build',
    '.pytest_cache',
    '.coverage',
    'htmlcov',
    'migrations',  # Django migrations
    'media',  # Django media files
    'static',  # Django static files
    'staticfiles'  # Django collected static
}

# Директории, содержимое которых не нужно читать
SKIP_CONTENT_READ = {
    'static',
    'staticfiles',
    'media',
    'assets'
}

# Служебные файлы Django и Python
EXCLUDE_FILES = {
    '.gitignore',
    'db.sqlite3',
    '.env',
    '.env.example',
    '.python-version',
    'Pipfile',
    'Pipfile.lock',
    'poetry.lock',
    'pyproject.toml',
    '.coverage',
    '.coveragerc',
    '.DS_Store',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
    '*.so'
}

# Список файлов для включения
INCLUDE_FILES = set()


def add_files_to_include(*file_paths):
    """Добавляет файлы в список включаемых файлов."""
    for file_path in file_paths:
        INCLUDE_FILES.add(os.path.normpath(file_path))
    return list(INCLUDE_FILES)


def get_formatted_size(file_path):
    """Форматирует размер файла в человекочитаемый вид."""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} GB"


def should_exclude(path):
    """Проверяет, должен ли путь быть исключен."""
    if os.path.normpath(path) in INCLUDE_FILES:
        return False

    path_parts = os.path.normpath(path).split(os.sep)

    # Проверка на исключаемые директории
    for part in path_parts:
        if part in EXCLUDE_DIRS:
            return True

    # Проверка на исключаемые файлы
    filename = os.path.basename(path)
    for pattern in EXCLUDE_FILES:
        if pattern.startswith('*'):
            if filename.endswith(pattern[1:]):
                return True
        elif filename == pattern:
            return True

    return False


def get_directory_tree(root_dir):
    """Генерирует дерево каталогов проекта."""
    tree = []
    root_name = os.path.basename(root_dir)
    tree.append(f"{root_name}/")

    for root, dirs, files in os.walk(root_dir, topdown=True):
        # Фильтрация директорий
        dirs[:] = [d for d in dirs
                   if d not in EXCLUDE_DIRS
                   and not d.startswith('.')]

        # Фильтрация файлов
        files = [f for f in files
                 if not any(f.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd'])
                 and f not in EXCLUDE_FILES
                 and not f.startswith('.')]

        if should_exclude(root):
            continue

        level = root[len(root_dir):].count(os.sep)
        indent = '│   ' * (level - 1) + ('├── ' if level > 0 else '')

        rel_path = os.path.relpath(root, root_dir)
        if rel_path != '.':
            tree.append(f"{indent}{os.path.basename(root)}/")

        file_indent = '│   ' * level + '├── '
        for f in sorted(files):
            file_path = os.path.join(root, f)
            size_str = get_formatted_size(file_path)
            tree.append(f"{file_indent}{f} ({size_str})")

    return '\n'.join(tree)


def get_files_paths(root_dir):
    """Возвращает список путей всех файлов проекта."""
    paths = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs
                   if d not in EXCLUDE_DIRS
                   and not d.startswith('.')]

        files = [f for f in files
                 if not any(f.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd'])
                 and f not in EXCLUDE_FILES
                 and not f.startswith('.')]

        if should_exclude(root):
            continue

        rel_path = os.path.relpath(root, root_dir)
        for f in sorted(files):
            if rel_path == '.':
                paths.append(f)
            else:
                paths.append(os.path.join(rel_path, f))

    return sorted(paths)


def scan_django_project(project_root):
    """Сканирует Django проект и выводит его структуру."""
    print("\n" + " СТРУКТУРА DJANGO ПРОЕКТА ".center(80, '='))
    print(get_directory_tree(project_root))

    print("\n" + " СПИСОК ФАЙЛОВ ПРОЕКТА ".center(80, '='))
    for path in get_files_paths(project_root):
        print(path)

    print("\n" + " СОДЕРЖИМОЕ ФАЙЛОВ ".center(80, '='))
    for root, dirs, files in os.walk(project_root):
        if any(skip_dir in root.split(os.sep) for skip_dir in SKIP_CONTENT_READ):
            continue

        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        files = [f for f in files
                 if f not in EXCLUDE_FILES
                 and not f.startswith('.')
                 and not any(f.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd'])]

        if should_exclude(root):
            continue

        for file in sorted(files):
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)

            # Пропускаем бинарные и медиа файлы
            if any(file.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif',
                                                  '.pdf', '.doc', '.docx', '.zip']):
                print(f"\n{' БИНАРНЫЙ ФАЙЛ: ' + rel_path + ' ':.^80}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"\n{' ФАЙЛ: ' + rel_path + ' ':.^80}")
                print(f"Размер: {get_formatted_size(file_path)}\n")
                print(content)
                print('\n' + '-' * 80)
            except UnicodeDecodeError:
                print(f"\n{' БИНАРНЫЙ ФАЙЛ: ' + rel_path + ' ':.^80}")
            except Exception as e:
                print(f"\nОшибка чтения {rel_path}: {str(e)}")


if __name__ == "__main__":
    # Укажите путь к корню вашего Django проекта
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Добавьте файлы для включения при необходимости
    # add_files_to_include("path/to/file1", "path/to/file2")

    scan_django_project(project_root)