# university/models/curriculum.py

from django.db import models
from .specialty import Specialty
from .department import Department


class Curriculum(models.Model):
    """
    Oʻquv rejasi (curriculum) – HEMIS curriculum-list endpointidan
    """
    api_id = models.BigIntegerField(unique=True)  # API dan "id"
    name = models.CharField(max_length=255, db_index=True)

    # Yangi: ForeignKey'lar
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,          # specialty o'chirilsa, curriculum qoladi
        null=True,
        blank=True,
        related_name='curriculums',
        db_index=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculums',
        db_index=True
    )

    education_year_name = models.CharField(max_length=50)
    education_year_current = models.BooleanField(default=False)

    education_type_name = models.CharField(max_length=100)
    education_form_name = models.CharField(max_length=100)

    marking_system_name = models.CharField(max_length=100, blank=True)
    marking_minimum_limit = models.IntegerField(null=True, blank=True)
    marking_gpa_limit = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    semester_count = models.PositiveIntegerField()
    education_period = models.PositiveIntegerField()  # yillarda

    self_hash = models.CharField(max_length=32, blank=True, db_index=True)
    accepted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.education_year_name})"

    class Meta:
        verbose_name = "Oʻquv rejasi"
        verbose_name_plural = "Oʻquv rejalar"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['specialty']),
            models.Index(fields=['department']),
        ]
        ordering = ['-education_year_name', 'name']
