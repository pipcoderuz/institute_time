from django.db import models
from .department import Department

class Specialty(models.Model):
    api_id = models.BigIntegerField(unique=True)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255, db_index=True)
    active = models.BooleanField(default=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='specialty',
        db_index=True
    )
    education_type_name = models.CharField(max_length=100)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    self_hash = models.CharField(max_length=32, blank=True, db_index=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.education_type_name})"

    class Meta:
        verbose_name = "Yoʻnalish"
        verbose_name_plural = "Yoʻnalishlar"
        indexes = [
            models.Index(fields=['name']),
        ]
