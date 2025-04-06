# directory/models/document_template.py
import os
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Настраиваем хранилище для файлов шаблонов: файлы будут сохраняться в MEDIA_ROOT/document_templates,
# а URL для доступа к ним будет /media/document_templates/
document_storage = FileSystemStorage(
    location=os.path.join(settings.MEDIA_ROOT, 'document_templates'),
    base_url=os.path.join(settings.MEDIA_URL, 'document_templates/')
)

class DocumentTemplate(models.Model):
    """
    📃 Модель для хранения шаблонов документов (DOCX файлы)

    Хранит информацию о шаблонах документов, которые используются
    для генерации документов на основе данных сотрудников.
    """

    # Типы документов
    DOCUMENT_TYPES = (
        ('all_orders', '📝 Распоряжения о стажировке'),
        ('knowledge_protocol', '📋 Протокол проверки знаний по охране труда'),
        ('doc_familiarization', '📝 Лист ознакомления с документами'),
        ('siz_card', '🛡️ Карточка учета СИЗ'),
        ('personal_ot_card', '👤 Личная карточка по ОТ'),
        ('journal_example', '📒 Образец заполнения журнала'),
    )

    name = models.CharField(_("Название шаблона"), max_length=255)
    description = models.TextField(_("Описание"), blank=True)
    document_type = models.CharField(
        _("Тип документа"),
        max_length=50,
        choices=DOCUMENT_TYPES
    )
    template_file = models.FileField(
        _("Файл шаблона"),
        upload_to='',  # Файл будет сохранён непосредственно в storage.location
        storage=document_storage
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    # Привязка к организации
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="document_templates",
        verbose_name=_("Организация"),
        null=True,
        blank=True,
        help_text=_("Организация, для которой предназначен шаблон. Если не указана, шаблон считается эталонным.")
    )
    is_default = models.BooleanField(
        verbose_name=_("Эталонный шаблон"),
        default=False,
        help_text=_("Указывает, является ли шаблон эталонным для всех организаций")
    )

    class Meta:
        verbose_name = _("Шаблон документа")
        verbose_name_plural = _("Шаблоны документов")
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['document_type'],
                condition=models.Q(is_default=True),
                name='unique_default_template_per_type'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"

    def clean(self):
        super().clean()
        # Проверяем, что не может быть одновременно эталонным и привязанным к организации
        if self.is_default and self.organization:
            raise ValidationError(
                {'is_default': _('Эталонный шаблон не может быть привязан к организации')}
            )




class GeneratedDocument(models.Model):
    """
    📄 Модель для хранения сгенерированных документов

    Хранит информацию о документах, сгенерированных на основе шаблонов.
    """
    template = models.ForeignKey(
        DocumentTemplate,
        verbose_name=_("Шаблон"),
        on_delete=models.SET_NULL,
        null=True
    )
    document_file = models.FileField(
        _("Файл документа"),
        upload_to='generated_documents/%Y/%m/%d/'
    )
    employee = models.ForeignKey(
        'directory.Employee',
        verbose_name=_("Сотрудник"),
        on_delete=models.CASCADE,
        related_name="documents"
    )
    created_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Создан пользователем"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    document_data = models.JSONField(
        _("Данные документа"),
        default=dict,
        blank=True,
        help_text=_("Данные, использованные для генерации документа")
    )

    class Meta:
        verbose_name = _("Сгенерированный документ")
        verbose_name_plural = _("Сгенерированные документы")
        ordering = ['-created_at']

    def __str__(self):
        return f"Документ для {self.employee} ({self.created_at.strftime('%d.%m.%Y')})"