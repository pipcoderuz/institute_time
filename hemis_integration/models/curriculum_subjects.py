# university/models/curriculum_subject.py

from django.db import models
from .curriculum import Curriculum
from .subjects import Subjects
from .department import Department


class CurriculumSubject(models.Model):
    """
    Oʻquv rejasidagi fan (curriculum-subject-list endpointidan)
    Bogʻlanishlar: Curriculum, SubjectMeta, Department
    """
    api_id = models.BigIntegerField(unique=True)  # API dan "id"

    # Bogʻlanishlar
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name='subjects',
        help_text="Bu fan qaysi oʻquv rejasiga tegishli"
    )
    subject = models.ForeignKey(
        Subjects,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculum_subjects',
        help_text="Fan meta-maʼlumoti (subject-meta-list dan)"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculum_subjects',
        help_text="Kafedra yoki boʻlim"
    )

    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, db_index=True)

    subject_type_name = models.CharField(max_length=100, blank=True)
    subject_block_name = models.CharField(max_length=100, blank=True)

    semester_name = models.CharField(max_length=50, blank=True)
    credit = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    self_hash = models.CharField(max_length=32, blank=True, db_index=True)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.code}) – {self.credit or '?'} kredit"

    class Meta:
        verbose_name = "Oʻquv rejasi fani"
        verbose_name_plural = "Oʻquv rejasi fanlari"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['active']),
        ]
        ordering = ['name']
