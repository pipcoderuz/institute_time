# from django.db import models
# from django.utils import timezone
# from accounts.models import CustomUser
# from .groups import Group


# class Student(models.Model):
#     hemis_id = models.BigIntegerField(unique=True)
#     hash_value = models.CharField(max_length=128, db_index=True)
#     status = models.CharField(max_length=10, choices=[('active', 'Faol'), ('inactive', 'Faol emas')], default='active')

#     full_name = models.CharField(max_length=255, db_index=True)
#     student_id_number = models.CharField(max_length=30, unique=True, db_index=True)
#     first_name = models.CharField(max_length=100)
#     second_name = models.CharField(max_length=100)
#     third_name = models.CharField(max_length=100, blank=True)
#     gender = models.CharField(max_length=20)
#     birth_date = models.DateField(null=True)
#     image = models.URLField(blank=True)

#     group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name='students')
#     specialty_name = models.CharField(max_length=255)
#     payment_form = models.CharField(max_length=50)
#     student_status = models.CharField(max_length=50)

#     updated_at_api = models.DateTimeField()
#     last_seen_at = models.DateTimeField(auto_now=True)

#     user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

#     raw_data = models.JSONField(null=True, blank=True)

#     class Meta:
#         indexes = [
#             models.Index(fields=['status', 'last_seen_at']),
#             models.Index(fields=['student_id_number']),
#         ]

#     def __str__(self):
#         return f"{self.full_name} ({self.student_id_number})"
