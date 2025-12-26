from django.db import models


class Group(models.Model):
    api_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    department_name = models.CharField(max_length=255)
    specialty_name = models.CharField(max_length=255)
    education_lang = models.CharField(max_length=50)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
