# setup_project.py
import os
import subprocess
import sys


def run_command(command):
    """Выполняет команду и выводит результат"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Команда выполнена успешно: {command}")
        if result.stdout:
            print("Вывод:")
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {command}")
        print(f"Код ошибки: {e.returncode}")
        print(f"Сообщение об ошибке:")
        print(e.stderr)
        sys.exit(1)


def setup_project():
    """Настраивает проект: миграции и статические файлы"""

    print("Начало настройки проекта...")

    # Создаем необходимые директории
    directories = ['static', 'media', 'staticfiles']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Директория '{directory}' создана или уже существует")

    # Выполняем миграции
    print("\nПрименение миграций...")
    commands = [
        'python manage.py makemigrations',
        'python manage.py migrate',
    ]

    for command in commands:
        run_command(command)

    # Собираем статические файлы
    print("\nСбор статических файлов...")
    run_command('python manage.py collectstatic --noinput')

    # Создаем суперпользователя, если его нет
    print("\nХотите создать суперпользователя? (y/n)")
    if input().lower() == 'y':
        run_command('python manage.py createsuperuser')

    print("\nНастройка проекта завершена успешно!")
    print("\nТеперь вы можете запустить сервер разработки командой:")
    print("python manage.py runserver")


if __name__ == "__main__":
    setup_project()