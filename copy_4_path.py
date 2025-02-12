import tkinter as tk
from tkinter import messagebox
import os
from pathlib import Path
import pyperclip


def get_selected_files():
    """Получает список путей выбранных файлов из буфера обмена."""
    try:
        clipboard_content = pyperclip.paste()
        print(f"Содержимое буфера обмена:\n{clipboard_content}")

        # PyCharm может копировать пути в разных форматах
        # Пробуем разные разделители
        if '\r\n' in clipboard_content:
            files = clipboard_content.split('\r\n')
        elif '\n' in clipboard_content:
            files = clipboard_content.split('\n')
        else:
            files = [clipboard_content]

        # Очищаем и конвертируем пути
        files = [Path(f.strip()) for f in files if f.strip()]

        # Проверяем существование файлов
        valid_files = []
        for f in files:
            if f.is_file():
                valid_files.append(f)
                print(f"Найден файл: {f}")
            else:
                print(f"Путь не является файлом или не существует: {f}")

        if not valid_files:
            print("Не найдено валидных файлов!")

        return valid_files
    except Exception as e:
        print(f"Ошибка при обработке буфера обмена: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось получить файлы из буфера обмена:\n{str(e)}")
        return []


def collect_file_contents(files):
    """Собирает содержимое всех файлов в один текст, добавляя пути."""
    result = []
    for file_path in files:
        try:
            print(f"Читаем файл: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                result.append(f"--- {file_path.absolute()} ---\n{content}\n") # Добавляем абсолютный путь
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {str(e)}")
            messagebox.showwarning("Предупреждение",
                                   f"Не удалось прочитать файл {file_path}:\n{str(e)}")
    return '\n'.join(result)


def save_result(content):
    """Сохраняет результат в буфер обмена и в файл."""
    if not content:
        print("Нет данных для сохранения")
        messagebox.showinfo("Информация", "Нет данных для сохранения")
        return

    # Сохраняем в буфер обмена
    pyperclip.copy(content)
    print("Результат скопирован в буфер обмена")

    # Сохраняем в файл
    output_path = Path.home() / 'collected_files.txt'
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Результат сохранен в файл: {output_path}")
        messagebox.showinfo("Успех",
                            f"Результат сохранен в буфер обмена и в файл:\n{output_path}")
    except Exception as e:
        print(f"Ошибка при сохранении в файл: {str(e)}")
        messagebox.showerror("Ошибка",
                             f"Не удалось сохранить в файл:\n{str(e)}\n\nНо данные доступны в буфере обмена")


def main():
    print("Запуск скрипта...")

    # Создаем скрытое окно tkinter (нужно для messagebox)
    root = tk.Tk()
    root.withdraw()

    # Получаем файлы
    files = get_selected_files()
    if not files:
        print("Файлы не найдены")
        messagebox.showinfo("Информация",
                            "Выделите файлы в PyCharm, скопируйте их (Ctrl+C) и запустите скрипт снова")
        return

    # Собираем содержимое
    content = collect_file_contents(files)

    # Сохраняем результат
    save_result(content)


if __name__ == '__main__':
    main()
    input("Нажмите Enter для завершения...")
