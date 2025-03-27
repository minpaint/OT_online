from django.db import models
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _

# Хранилище файлов для шаблонов документов
document_storage = FileSystemStorage(location='media/document_templates/')

class DocumentTemplate(models.Model):
    """
    📃 Модель для хранения шаблонов документов (DOCX файлы)
    
    Хранит информацию о шаблонах документов, которые используются 
    для генерации документов на основе данных сотрудников.
    """
    
    # Типы документов
    DOCUMENT_TYPES = (
        ('internship_order', '🔖 Распоряжение о стажировке'),
        ('admission_order', '🔖 Распоряжение о допуске к самостоятельной работе'),
        ('knowledge_protocol', '📋 Протокол проверки знаний по охране труда'),
        ('doc_familiarization', '📝 Лист ознакомления с документами'),
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
        upload_to='document_templates/', 
        storage=document_storage
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)
    
    class Meta:
        verbose_name = _("Шаблон документа")
        verbose_name_plural = _("Шаблоны документов")
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"


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