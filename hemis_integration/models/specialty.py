from django.db import models


class Specialty(models.Model):
    api_id = models.BigIntegerField(unique=True)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255, db_index=True)
    active = models.BooleanField(default=True)

    department_name = models.CharField(max_length=255)
    education_type_name = models.CharField(max_length=100)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.education_type_name})"

    class Meta:
        verbose_name = "Yoʻnalish"
        verbose_name_plural = "Yoʻnalishlar"
        indexes = [
            models.Index(fields=['name']),
        ]
