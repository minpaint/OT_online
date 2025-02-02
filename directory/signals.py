from django.db.models.signals import post_save
from django.dispatch import receiver
from directory.models import Employee, Position, StructuralSubdivision

@receiver(post_save, sender=Position)
def update_employee_subdivision(sender, instance, **kwargs):
    """
    Обновляет подразделение у сотрудников при изменении подразделения должности.
    Если для должности указано подразделение, то все сотрудники с данной позицией,
    у которых поле subdivision не заполнено, получают это значение.
    """
    if instance.subdivision:
        Employee.objects.filter(
            position=instance,
            subdivision__isnull=True
        ).update(subdivision=instance.subdivision)

@receiver(post_save, sender=StructuralSubdivision)
def update_departments(sender, instance, **kwargs):
    """
    Обновляет организацию в отделах при изменении организации подразделения.
    Использует related_name 'departments', если он задан, иначе – стандартное department_set.
    """
    # Проверяем, есть ли у instance атрибут 'departments'
    if hasattr(instance, 'departments'):
        instance.departments.all().update(organization=instance.organization)
    else:
        instance.department_set.all().update(organization=instance.organization)
