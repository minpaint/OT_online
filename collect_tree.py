from pathlib import Path
from typing import Iterator


class DirectoryTree:
    # Список директорий и файлов, которые нужно игнорировать
    IGNORE_DIRS = {
        '__pycache__',
        'migrations',
        '.git',
        '.idea',
        '.venv',
        'env',
        '.pytest_cache',
        'node_modules'
    }

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.tree_str = ""

    def generate(self) -> str:
        """Генерирует древовидную структуру директорий"""
        self.tree_str = f"📁 {self.root_dir.name}\n"
        self._walk_dir(self.root_dir, prefix="", level=0)
        return self.tree_str

    def _walk_dir(self, current_dir: Path, prefix: str, level: int) -> None:
        """Рекурсивно обходит директории и формирует строку дерева"""
        # Получаем отсортированный список всех элементов директории
        entries = sorted(
            [entry for entry in current_dir.iterdir()
             if entry.name not in self.IGNORE_DIRS and not entry.name.startswith('.')],
            key=lambda x: (not x.is_dir(), x.name.lower())
        )

        # Обрабатываем каждый элемент
        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1
            connector = "└──" if is_last else "├──"

            # Добавляем элемент в дерево
            self.tree_str += f"{prefix}{connector} {'📁' if entry.is_dir() else '📄'} {entry.name}\n"

            # Если это директория, рекурсивно обходим её
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                self._walk_dir(entry, prefix + extension, level + 1)


def main():
    # Получаем текущую директорию
    current_dir = Path.cwd()

    # Создаем экземпляр класса и генерируем дерево
    tree = DirectoryTree(current_dir)
    result = tree.generate()

    # Выводим результат
    print(result)


if __name__ == "__main__":
    main()