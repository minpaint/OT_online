from typing import List, Optional
from django.db.models import Q
from core.models import Employee, Division

class EmployeeService:
    @staticmethod
    def get_employees(division_id: Optional[int] = None, search_term: Optional[str] = None) -> List[Employee]:
        """
        Получить список сотрудников с возможностью фильтрации по подразделению и поиска
        """
        queryset = Employee.objects.all()

        if division_id:
            queryset = queryset.filter(division_id=division_id)

        if search_term:
            queryset = queryset.filter(
                Q(last_name__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(middle_name__icontains=search_term)
            )

        return queryset.order_by('last_name', 'first_name')

    @staticmethod
    def get_employee_by_id(employee_id: int) -> Optional[Employee]:
        """
        Получить сотрудника по ID
        """
        try:
            return Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return None

    @staticmethod
    def create_employee(data: dict) -> Employee:
        """
        Создать нового сотрудника
        """
        return Employee.objects.create(**data)

    @staticmethod
    def update_employee(employee: Employee, data: dict) -> Employee:
        """
        Обновить данные сотрудника
        """
        for key, value in data.items():
            setattr(employee, key, value)
        employee.save()
        return employee

    @staticmethod
    def delete_employee(employee: Employee) -> bool:
        """
        Удалить сотрудника
        """
        try:
            employee.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_employees_by_division(division: Division) -> List[Employee]:
        """
        Получить всех сотрудников подразделения
        """
        return Employee.objects.filter(division=division).order_by('last_name', 'first_name')
