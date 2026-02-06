from django.db import models


class Department(models.Model):
    """
    Fakultet, Kafedra, Boʻlim va boshqa tuzilmalar
    Self-referential (ierarxik) – parent orqali
    """
    api_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=100, unique=True)

    structure_type_name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    self_hash = models.CharField(max_length=32, blank=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Boʻlim"
        verbose_name_plural = "Boʻlimlar"
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['name']
