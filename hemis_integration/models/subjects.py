# university/models/subject_meta.py

from django.db import models


class Subjects(models.Model):
    """
    Fan meta-maʼlumotlari – HEMIS subject-meta-list endpointidan
    (fanlarning umumiy katalogi, oʻquv rejasidan mustaqil)
    """
    api_id = models.BigIntegerField(unique=True)  # API dan "id"
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)

    # "Majburiy fanlar" va h.k.
    subject_group_name = models.CharField(max_length=100, blank=True)
    education_type_name = models.CharField(max_length=100, blank=True)  # "Bakalavr", "Magistr"

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.education_type_name or 'nomaʼlum'})"

    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']
