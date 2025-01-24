from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
# Исправляем импорт - используем родительский пакет
from core.models import Employee, Organization, Department, Division, Position

@receiver(pre_save, sender=Employee)
def employee_pre_save(sender, instance, **kwargs):
    """
    Сигнал перед сохранением сотрудника
    - Автоматически заполняет организацию, подразделение и отдел из должности
    """
    if instance.position:
        instance.organization = instance.position.organization
        instance.department = instance.position.department
        instance.division = instance.position.division

@receiver(post_save, sender=Organization)
def organization_post_save(sender, instance, created, **kwargs):
    """
    Сигнал после сохранения организации
    """
    if created:
        # Здесь можно добавить логику при создании организации
        pass

@receiver(post_save, sender=Department)
def department_post_save(sender, instance, created, **kwargs):
    """
    Сигнал после сохранения подразделения
    """
    if created:
        # Здесь можно добавить логику при создании подразделения
        pass

@receiver(post_save, sender=Division)
def division_post_save(sender, instance, created, **kwargs):
    """
    Сигнал после сохранения отдела
    """
    if created:
        # Здесь можно добавить логику при создании отдела
        pass

@receiver(post_save, sender=Position)
def position_post_save(sender, instance, created, **kwargs):
    """
    Сигнал после сохранения должности
    - Обновляет связанных сотрудников при изменении организации/подразделения
    """
    Employee.objects.filter(position=instance).update(
        organization=instance.organization,
        department=instance.department,
        division=instance.division
    )