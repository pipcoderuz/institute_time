# university/models/curriculum.py

from django.db import models


class Curriculum(models.Model):
    """
    Oʻquv rejasi (curriculum) – HEMIS curriculum-list endpointidan
    """
    api_id = models.BigIntegerField(unique=True)  # API dan "id"
    name = models.CharField(max_length=255, db_index=True)

    specialty_name = models.CharField(max_length=255)
    department_name = models.CharField(max_length=255)

    education_year_name = models.CharField(max_length=50)
    education_year_current = models.BooleanField(default=False)

    education_type_name = models.CharField(max_length=100)
    education_form_name = models.CharField(max_length=100)

    marking_system_name = models.CharField(max_length=100, blank=True)
    marking_minimum_limit = models.IntegerField(null=True, blank=True)
    marking_gpa_limit = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    semester_count = models.PositiveIntegerField()
    education_period = models.PositiveIntegerField()  # yillarda

    accepted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.education_year_name})"

    class Meta:
        verbose_name = "Oʻquv rejasi"
        verbose_name_plural = "Oʻquv rejalar"
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['-education_year_name', 'name']
