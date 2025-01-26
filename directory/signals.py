from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from directory.models import Employee, Position, StructuralSubdivision

@receiver(post_save, sender=Position)
def update_employee_subdivision(sender, instance, **kwargs):
    """
    Обновляет подразделение у сотрудников при изменении подразделения должности.
    """
    if instance.subdivision:
        Employee.objects.filter(
            position=instance,
            structural_subdivision__isnull=True
        ).update(structural_subdivision=instance.subdivision)

@receiver(post_save, sender=StructuralSubdivision)
def update_departments(sender, instance, **kwargs):
    """
    Обновляет организацию в отделах при изменении организации подразделения.
    """
    instance.departments.all().update(organization=instance.organization)