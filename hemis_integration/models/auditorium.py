# university/models/auditorium.py

from django.db import models


class Auditorium(models.Model):
    """
    Auditoriya (xona) modeli.
    """
    code = models.CharField(max_length=50, unique=True,
                            db_index=True)  # "code" unique
    name = models.CharField(max_length=255, db_index=True)

    # "Ma’ruza", "Seminar" va h.k.
    auditorium_type_name = models.CharField(max_length=100)
    building_name = models.CharField(max_length=255)
    volume = models.PositiveIntegerField()  # sigʻim (oʻrin soni)

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code}) – {self.volume} oʻrin"

    class Meta:
        verbose_name = "Auditoriya"
        verbose_name_plural = "Auditoriyalar"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['building_name']),
        ]
        ordering = ['building_name', 'name']
