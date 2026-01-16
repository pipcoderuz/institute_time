# university/management/commands/upload_curriculum_subjects.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

from hemis_integration.sync_apis.curriculum_subjects_data import sync_curriculum_subjects


class Command(BaseCommand):
    help = "HEMISdan oʻquv rejasi fanlarini (curriculum-subject-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        python manage.py upload_curriculum_subjects
        """
        start_time = timezone.now()
        self.stdout.write(
            "HEMIS oʻquv rejasi fanlari sinxronizatsiyasi boshlandi...")

        result = asyncio.run(sync_curriculum_subjects())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Oʻquv rejasi fanlari muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy fanlar soni: {result['total_subjects']}\n"
                f"  Yangi qoʻshilgan fanlar soni: {result['created']}\n"
                f"  Maʼlumoti yangilangan fanlar soni: {result['updated']}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan fanlar soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
