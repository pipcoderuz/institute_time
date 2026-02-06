from django.db import models
from .specialty import Specialty
from .department import Department


class Group(models.Model):
    api_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group',
        db_index=True
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,          # specialty o'chirilsa, curriculum qoladi
        null=True,
        blank=True,
        related_name='group',
        db_index=True
    )

    education_lang = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    self_hash = models.CharField(max_length=32, blank=True, db_index=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['specialty']),
            models.Index(fields=['department']),
        ]
