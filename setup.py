#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project_name.settings")
django.setup()

from directory.models import CommissionMember

problematic_members = CommissionMember.objects.filter(commission_id=4)
print(f"Найдено {problematic_members.count()} проблемных записей")
problematic_members.delete()
print("Проблемные записи удалены")