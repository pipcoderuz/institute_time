# university/models/student.py
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from .groups import Group
from .specialty import Specialty
from .curriculum import Curriculum
from .department import Department


class Student(models.Model):
    """
    Talaba – HEMIS student-list endpointidan
    """
    api_id = models.BigIntegerField(unique=True)  # "id"
    self_created_hash_value = models.CharField(max_length=64, db_index=True)  # oʻzgarish aniqlash uchun

    full_name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    third_name = models.CharField(max_length=100, blank=True)

    hemis_student_id_number = models.CharField(max_length=20, unique=True, db_index=True)
    student_passport_id = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)

    image = models.URLField(blank=True)
    image_full = models.URLField(blank=True)

    country_name = models.CharField(max_length=100, blank=True)
    province_name = models.CharField(max_length=100, blank=True)
    district_name = models.CharField(max_length=100, blank=True)
    citizenship_name = models.CharField(max_length=100, blank=True)

    student_status_name = models.CharField(max_length=100, blank=True)
    education_form_name = models.CharField(max_length=100, blank=True)
    education_type_name = models.CharField(max_length=100, blank=True)
    payment_form_name = models.CharField(max_length=100, blank=True)
    student_type_name = models.CharField(max_length=100, blank=True)

    # Bogʻlanishlar (ForeignKey)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    # Django user bilan bogʻlanish
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')

    # Qoʻshimcha
    avg_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_credit = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    year_of_enter = models.PositiveIntegerField(null=True, blank=True)
    level_name = models.CharField(max_length=50, blank=True)
    education_year_name = models.CharField(max_length=50, blank=True)

    updated_at_api = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    
    active = models.BooleanField(default=True)

    # agar toʻliq saqlamoqchi boʻlsangiz
    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.hemis_student_id_number or self.api_id})"

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"
        indexes = [
            models.Index(fields=['hemis_student_id_number']),
            models.Index(fields=['student_passport_id']),
            models.Index(fields=['full_name']),
            models.Index(fields=['active']),
            models.Index(fields=['last_synced_at']),
        ]