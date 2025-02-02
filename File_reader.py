import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from dataclasses import dataclass


@dataclass
class ProjectStats:
    """Статистика проекта"""
    total_files: int = 0
    python_files: int = 0
    template_files: int = 0
    js_files: int = 0


class DjangoAnalyzer:
    """Анализатор Django проекта"""

    IMPORTANT_FILES = {
        'models.py': 'Models definitions',
        'views.py': 'Views and logic',
        'urls.py': 'URL patterns',
        'forms.py': 'Forms processing',
        'admin.py': 'Admin interface',
        'apps.py': 'App configuration',
        '__init__.py': 'Package initialization',
        'settings.py': 'Project settings',
        'managers.py': 'Model managers',
        'services.py': 'Business logic',
        'utils.py': 'Utility functions',
        'tasks.py': 'Background tasks',
        'serializers.py': 'API serializers',
        'viewsets.py': 'API viewsets',
        'signals.py': 'Signal handlers',
        'middleware.py': 'Custom middleware',
        'context_processors.py': 'Template context',
        'validators.py': 'Custom validators',
        'filters.py': 'Query filters'
    }

    EXCLUDED_DIRS = {
        # Стандартные технические директории
        '__pycache__',
        'migrations',
        'tests',
        'venv',
        '.git',
        '.idea',
        'env',
        'node_modules',

        # Полностью исключаем staticfiles
        'staticfiles',

        # Другие статические директории
        'static/admin',
        'static/vendor',
        'assets/vendor',

        # Скомпилированные файлы и кэш
        '.sass-cache',
        'dist',
        'build',

        # Медиа файлы
        'media',

        # Локальные настройки разработки
        '.vscode',
        '.env',

        # Временные файлы
        'tmp',
        'temp'
    }

    # Расширяем список игнорируемых файлов
    EXCLUDED_FILES = {
        # Минифицированные файлы
        '.min.js',
        '.min.css',

        # Карты исходников
        '.map',

        # Конфигурационные файлы
        'package.json',
        'package-lock.json',
        'yarn.lock',
        'webpack.config.js',

        # Кэш и временные файлы
        '.pyc',
        '.pyo',
        '.pyd',
        '.so',
        '.dll',

        # Файлы документации
        'README.md',
        'LICENSE',

        # Файлы зависимостей
        'requirements.txt',
        'Pipfile',
        'Pipfile.lock'
    }

    def __init__(self, project_root: str):
        """Инициализация анализатора"""
        self.project_root = Path(project_root)
        self.stats = ProjectStats()
        self.setup_logging()

    def setup_logging(self) -> None:
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _should_exclude_file(self, filename: str) -> bool:
        """Проверяет, должен ли файл быть исключен из анализа"""
        return any(filename.endswith(ext) for ext in self.EXCLUDED_FILES)

    def analyze(self) -> Dict[str, Any]:
        """Анализ проекта"""
        logging.info(f"Starting analysis of {self.project_root}")

        structure = {
            'structure': self._get_structure(),
            'contents': self._get_contents(),
            'stats': self._get_stats()
        }

        return structure

    def _get_structure(self) -> Dict[str, Any]:
        """Получение структуры проекта с улучшенной фильтрацией"""
        structure = {}

        for root, dirs, files in os.walk(self.project_root):
            # Улучшенная фильтрация директорий
            dirs[:] = [d for d in dirs if not any(
                (d.lower() == excluded.lower() or  # Точное совпадение
                 excluded.lower() in str(Path(root) / d).lower() or  # Путь содержит исключаемую директорию
                 str(Path(root) / d).lower().endswith(excluded.lower()))  # Путь заканчивается на исключаемую директорию
                for excluded in self.EXCLUDED_DIRS
            )]

            path = Path(root)

            # Пропускаем обработку, если текущая директория должна быть исключена
            if any(excluded.lower() in str(path).lower() for excluded in self.EXCLUDED_DIRS):
                continue

            rel_path = path.relative_to(self.project_root)

            if str(rel_path) == '.':
                current_dict = structure
            else:
                current_dict = structure
                for part in rel_path.parts:
                    current_dict = current_dict.setdefault(part, {})

            # Фильтруем файлы
            important_files = [
                f for f in files
                if (f.endswith(('.html', '.js', '.py')) and
                    not self._should_exclude_file(f))
            ]

            if important_files:
                current_dict['_files'] = important_files
                self.stats.total_files += len(important_files)

                for f in important_files:
                    if f.endswith('.py'):
                        self.stats.python_files += 1
                    elif f.endswith('.html'):
                        self.stats.template_files += 1
                    elif f.endswith('.js'):
                        self.stats.js_files += 1

        return structure

    def _get_contents(self) -> Dict[str, str]:
        """Получение содержимого файлов"""
        contents = {}

        for root, _, files in os.walk(self.project_root):
            path = Path(root)

            # Пропускаем исключенные директории
            if any(excluded.lower() in str(path).lower() for excluded in self.EXCLUDED_DIRS):
                continue

            for file in files:
                # Пропускаем исключенные файлы
                if self._should_exclude_file(file):
                    continue

                if (file in self.IMPORTANT_FILES or
                        file.endswith(('.html', '.js', '.py'))):

                    file_path = path / file
                    rel_path = file_path.relative_to(self.project_root)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            contents[str(rel_path)] = f.read()
                    except Exception as e:
                        logging.error(f"Error reading {file_path}: {e}")
                        contents[str(rel_path)] = f"Error reading file: {e}"

        return contents

    def _get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        return {
            'total_files': self.stats.total_files,
            'python_files': self.stats.python_files,
            'template_files': self.stats.template_files,
            'js_files': self.stats.js_files
        }

    def print_structure(self, structure: Dict[str, Any], indent: int = 0) -> None:
        """Вывод структуры проекта"""
        for key, value in sorted(structure.items()):
            if key == '_files':
                for file in sorted(value):
                    desc = self.IMPORTANT_FILES.get(file, '')
                    desc_text = f" - {desc}" if desc else ''
                    print(f"{'│ ' * (indent - 1)}├── {file}{desc_text}")
            else:
                print(f"{'│ ' * indent}├── {key}/")
                if isinstance(value, dict):
                    self.print_structure(value, indent + 1)

    def print_contents(self, contents: Dict[str, str]) -> None:
        """Вывод содержимого файлов"""
        for file_path, content in sorted(contents.items()):
            print(f"\n{'=' * 80}")
            print(f"File: {file_path}")
            print('=' * 80)
            print(content)
            print('=' * 80)

    def save_analysis(self, results: Dict[str, Any], output_file: str) -> None:
        """Сохранение результатов анализа в JSON файл"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            logging.info(f"Analysis results saved to {output_file}")
        except Exception as e:
            logging.error(f"Error saving analysis results: {e}")


def main():
    """Основная функция"""
    # Указываем конкретный путь к проекту
    project_root = r"d:\YandexDisk\OT_online"

    # Имя файла для сохранения результатов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(project_root, f"django_analysis_{timestamp}.json")

    try:
        analyzer = DjangoAnalyzer(project_root)
        results = analyzer.analyze()

        print("\n=== DJANGO PROJECT STRUCTURE ===")
        analyzer.print_structure(results['structure'])

        print("\n=== STATISTICS ===")
        for key, value in results['stats'].items():
            print(f"{key}: {value}")

        print("\n=== FILE CONTENTS ===")
        analyzer.print_contents(results['contents'])

        # Сохраняем результаты в файл
        analyzer.save_analysis(results, output_file)
        print(f"\nAnalysis results saved to: {output_file}")

    except Exception as e:
        logging.error(f"Error analyzing project: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()