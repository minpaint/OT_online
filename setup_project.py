import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


class DjangoProjectAnalyzer:
    """
    Класс для анализа структуры и содержимого Django проекта.
    Обеспечивает вывод в древовидном формате и детальный анализ кода.
    """

    def __init__(self, project_root: str):
        """
        Инициализация анализатора

        Args:
            project_root (str): Путь к корневой директории Django проекта
        """
        self.project_root = Path(project_root)
        self.cache = {}
        self.setup_config()
        self.setup_logging()

    def setup_config(self) -> None:
        """Настройка базовой конфигурации для анализа проекта"""
        self.config = {
            'main_directories': {
                'models': {
                    'description': 'Модели данных',
                    'patterns': ['*.py'],
                    'important_files': [
                        'document.py',
                        'employee.py',
                        'equipment.py',
                        'organization.py',
                        'position.py',
                        'subdivision.py',
                        'department.py'
                    ]
                },
                'views': {
                    'description': 'Представления',
                    'patterns': ['*.py'],
                    'important_files': [
                        'views.py',
                        'employees.py',
                        'positions.py'
                    ]
                },
                'templates': {
                    'description': 'Шаблоны',
                    'patterns': ['*.html'],
                    'important_files': [
                        'base.html',
                        'home.html'
                    ]
                },
                'static/js': {
                    'description': 'JavaScript файлы',
                    'patterns': ['*.js'],
                    'important_files': [
                        'admin_dependent_dropdowns.js',
                        'custom_dynamic_forms.js',
                        'main.js'
                    ]
                }
            },
            'excluded_patterns': [
                '__pycache__',
                '.git',
                '.idea',
                'venv',
                'migrations',
                'tests',
                '.env',
                '.DS_Store',
                '*.pyc',
                'db.sqlite3'
            ],
            'file_descriptions': {
                'urls.py': 'URL маршрутизация',
                'views.py': 'Основные представления',
                'models.py': 'Основные модели',
                'forms.py': 'Формы для обработки данных',
                'admin.py': 'Настройки админ-панели',
                'document.py': 'Модель документов',
                'employee.py': 'Модель сотрудников',
                'equipment.py': 'Модель оборудования',
                'organization.py': 'Модель организации',
                'position.py': 'Модель должностей',
                'subdivision.py': 'Модель подразделений',
                'department.py': 'Модель отделов',
                'custom_dynamic_forms.js': 'Динамические формы',
                'admin_dependent_dropdowns.js': 'Зависимые списки в админке',
                'main.js': 'Основной JavaScript файл'
            }
        }

    def setup_logging(self) -> None:
        """Настройка системы логирования"""
        logging.basicConfig(
            filename=f'django_analyzer_{datetime.now():%Y%m%d}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def analyze_project(self) -> Tuple[str, dict]:
        """
        Проводит полный анализ проекта

        Returns:
            Tuple[str, dict]: (древовидная структура, полные данные анализа)
        """
        try:
            structure = self._analyze_structure()
            tree_output = self._format_tree_output(structure)
            return tree_output, structure
        except Exception as e:
            logging.error(f"Ошибка при анализе проекта: {e}")
            raise

    def _analyze_structure(self) -> Dict[str, Any]:
        """
        Анализирует структуру проекта и содержимое файлов

        Returns:
            Dict[str, Any]: Структура проекта с данными анализа
        """
        structure = {'directories': {}, 'files': {}}

        for root, dirs, files in os.walk(self.project_root):
            # Пропускаем исключенные директории
            dirs[:] = [d for d in dirs if not any(
                pattern in d for pattern in self.config['excluded_patterns']
            )]

            current_path = Path(root)
            rel_path = current_path.relative_to(self.project_root)

            # Анализируем только нужные директории и файлы
            if self._should_analyze_directory(rel_path):
                dir_structure = structure['directories'].setdefault(str(rel_path), {
                    'path': str(rel_path),
                    'type': self._get_directory_type(rel_path),
                    'files': {}
                })

                for file in files:
                    if self._should_analyze_file(rel_path, file):
                        file_path = current_path / file
                        file_data = self._analyze_file(file_path, rel_path)
                        dir_structure['files'][file] = file_data

        return structure

    def _should_analyze_directory(self, path: Path) -> bool:
        """Проверяет, нужно ли анализировать директорию"""
        path_str = str(path)
        return any(
            dir_name in path_str
            for dir_name in self.config['main_directories'].keys()
        )

    def _should_analyze_file(self, dir_path: Path, filename: str) -> bool:
        """Проверяет, нужно ли анализировать файл"""
        if any(pattern in filename for pattern in self.config['excluded_patterns']):
            return False

        dir_type = self._get_directory_type(dir_path)
        if dir_type in self.config['main_directories']:
            dir_config = self.config['main_directories'][dir_type]
            return (
                    filename in dir_config.get('important_files', []) or
                    any(
                        self._match_pattern(filename, pattern)
                        for pattern in dir_config['patterns']
                    )
            )
        return False

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Проверяет соответствие файла паттерну"""
        from fnmatch import fnmatch
        return fnmatch(filename, pattern)

    def _get_directory_type(self, path: Path) -> str:
        """Определяет тип директории"""
        path_str = str(path)
        for dir_type in self.config['main_directories'].keys():
            if dir_type in path_str:
                return dir_type
        return 'other'

    def _analyze_file(self, file_path: Path, rel_path: Path) -> Dict[str, Any]:
        """
        Анализирует содержимое файла

        Args:
            file_path (Path): Полный путь к файлу
            rel_path (Path): Относительный путь от корня проекта

        Returns:
            Dict[str, Any]: Данные анализа файла
        """
        try:
            stats = file_path.stat()

            # Читаем содержимое файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                content = "Бинарный файл"
            except Exception as e:
                content = f"Ошибка чтения файла: {str(e)}"

            return {
                'path': str(rel_path / file_path.name),
                'size': self._format_size(stats.st_size),
                'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'description': self.config['file_descriptions'].get(file_path.name, ''),
                'content': content,
                'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
            }
        except Exception as e:
            logging.error(f"Ошибка при анализе файла {file_path}: {e}")
            return {'error': str(e)}

    def _format_size(self, size_bytes: int) -> str:
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _format_tree_output(self, structure: Dict[str, Any]) -> str:
        """Форматирует структуру в древовидный вывод"""
        output = ["СТРУКТУРА DJANGO ПРОЕКТА", "=" * 50, ""]

        for dir_path, dir_data in sorted(structure['directories'].items()):
            # Добавляем информацию о директории
            indent = "    " * (dir_path.count('/') + 1)
            output.append(f"{indent[:-4]}├── {os.path.basename(dir_path)}/")

            if dir_data['type'] in self.config['main_directories']:
                desc = self.config['main_directories'][dir_data['type']]['description']
                output.append(f"{indent}└── Описание: {desc}")

            # Добавляем информацию о файлах
            for filename, file_data in sorted(dir_data['files'].items()):
                output.append(f"{indent}├── {filename} ({file_data['size']})")
                if file_data['description']:
                    output.append(f"{indent}│   └── {file_data['description']}")

        return "\n".join(output)

    def save_analysis(self, output_path: str = 'django_project_analysis.json') -> None:
        """Сохраняет результаты анализа в JSON файл"""
        try:
            _, structure = self.analyze_project()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            print(f"\nПолный анализ сохранен в: {output_path}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении анализа: {e}")
            raise

    def print_file_contents(self, structure: Dict[str, Any]) -> None:
        """Выводит содержимое всех проанализированных файлов"""
        print("\nСОДЕРЖИМОЕ ФАЙЛОВ:")
        print("=" * 50)

        for dir_path, dir_data in sorted(structure['directories'].items()):
            for filename, file_data in sorted(dir_data['files'].items()):
                print(f"\n{'=' * 80}")
                print(f"--- {file_data['path']} ---")
                if file_data['description']:
                    print(f"Описание: {file_data['description']}")
                print(f"Размер: {file_data['size']}")
                print(f"Последнее изменение: {file_data['modified']}")
                print("=" * 80)
                print(file_data['content'])


def main():
    """Основная функция для запуска анализатора"""
    project_root = "D:/YandexDisk/OT_online"  # Укажите путь к вашему проекту

    try:
        # Создаем анализатор
        analyzer = DjangoProjectAnalyzer(project_root)

        # Получаем структуру и данные анализа
        tree_output, structure = analyzer.analyze_project()

        # Выводим древовидную структуру
        print(tree_output)

        # Выводим содержимое файлов
        analyzer.print_file_contents(structure)

        # Сохраняем полный анализ в JSON
        analyzer.save_analysis()

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        logging.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()