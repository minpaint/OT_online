from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class StructuralSubdivision(MPTTModel):
    """
    🏭 Модель для хранения структурных подразделений.
    Использует MPTT для организации иерархической структуры.
    """
    name = models.CharField(
        "Наименование",
        max_length=255
    )
    short_name = models.CharField(
        "Сокращенное наименование",
        max_length=255,
        blank=True
    )
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.PROTECT,
        related_name="subdivisions",
        verbose_name="Организация"
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительское подразделение"
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"
        ordering = ['name']
        unique_together = ['name', 'organization']

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_ru})"

    def get_ancestors_list(self):
        """Получить список всех предков"""
        return [ancestor.name for ancestor in self.get_ancestors(include_self=False)]

    def get_full_path(self):
        """Получить полный путь подразделения"""
        ancestors = self.get_ancestors_list()
        ancestors.append(self.name)
        return ' → '.join(ancestors)