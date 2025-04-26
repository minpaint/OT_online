#!/usr/bin/env python
import os
import sys
import inspect

# 📌 Monkeypatch для Python 3.11+ (совместимость pymorphy2 и других библиотек)
if not hasattr(inspect, 'getargspec'):
    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return spec.args, spec.varargs, spec.varkw, spec.defaults
    inspect.getargspec = getargspec

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()