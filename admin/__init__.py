from django.contrib import admin
from directory.models.organization import Organization
from directory.models.subdivision import StructuralSubdivision
from directory.models.department import Department
from directory.models.document import Document
from directory.models.equipment import Equipment
from directory.models.position import Position
from directory.models.employee import Employee

# Регистрация моделей в админке
admin.site.register(Organization)
admin.site.register(StructuralSubdivision)
admin.site.register(Department)
admin.site.register(Document)
admin.site.register(Equipment)
admin.site.register(Position)
admin.site.register(Employee)