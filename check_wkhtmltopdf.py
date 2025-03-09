#!/usr/bin/env python
"""
Скрипт для проверки установки wkhtmltopdf
"""
import subprocess
import os
import sys


def check_wkhtmltopdf():
    """Проверяет, установлен ли wkhtmltopdf и доступен ли он в системе."""
    try:
        # Пытаемся выполнить команду wkhtmltopdf --version
        process = subprocess.Popen(
            ['wkhtmltopdf', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        # Проверяем результат
        if process.returncode == 0:
            version = stdout.decode('utf-8').strip()
            print(f"✅ wkhtmltopdf установлен: {version}")
            return True
        else:
            print("❌ wkhtmltopdf не найден в PATH")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке wkhtmltopdf: {e}")
        return False


def find_wkhtmltopdf():
    """Пытается найти wkhtmltopdf в стандартных местах."""
    common_paths = [
        # Linux/Unix
        '/usr/bin/wkhtmltopdf',
        '/usr/local/bin/wkhtmltopdf',
        # Windows
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
    ]

    found_paths = []
    for path in common_paths:
        if os.path.exists(path) and os.path.isfile(path):
            found_paths.append(path)

    if found_paths:
        print("🔍 wkhtmltopdf найден в следующих местах:")
        for path in found_paths:
            print(f"   - {path}")
        print(f"\nДобавьте в settings.py: WKHTMLTOPDF_CMD = '{found_paths[0]}'")
    else:
        print("🔍 wkhtmltopdf не найден в стандартных местах.")
        if os.name == 'nt':  # Windows
            print("\nДля Windows скачайте установщик с https://wkhtmltopdf.org/downloads.html")
        else:  # Linux/Unix
            if os.path.exists('/etc/debian_version'):
                print("\nУстановите с помощью команды: sudo apt-get install wkhtmltopdf")
            elif os.path.exists('/etc/redhat-release'):
                print("\nУстановите с помощью команды: sudo yum install wkhtmltopdf")
            else:
                print("\nУстановите wkhtmltopdf через пакетный менеджер вашей системы.")


if __name__ == "__main__":
    print("🔍 Проверка установки wkhtmltopdf...")
    if not check_wkhtmltopdf():
        find_wkhtmltopdf()

    print("\n💡 Подсказка: Если wkhtmltopdf установлен, но не найден в PATH,")
    print("   укажите полный путь к нему в settings.py:")
    print("   WKHTMLTOPDF_CMD = '/путь/к/wkhtmltopdf'")