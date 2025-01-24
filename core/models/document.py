from django.db import models
from .organizational_unit import OrganizationalUnit


class Document(models.Model):
    """Документы"""

    DOCUMENT_TYPES = [
        ('instruction', 'Инструкция'),
        ('protocol', 'Протокол'),
        ('certificate', 'Удостоверение'),
        ('order', 'Приказ'),
        ('other', 'Прочее'),
    ]

    title = models.CharField('Название', max_length=255)
    document_type = models.CharField(
        'Тип документа',
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    file = models.FileField('Файл', upload_to='documents/%Y/%m/')

    # Связь с организационной структурой
    organizational_unit = models.ForeignKey(
        OrganizationalUnit,
        on_delete=models.CASCADE,
        verbose_name='Подразделение'
    )

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"