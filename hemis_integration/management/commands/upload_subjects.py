# university/management/commands/upload_subject_metas.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

from hemis_integration.sync_apis.subjects_data import sync_subjects


class Command(BaseCommand):
    help = "HEMISdan fan meta-maʼlumotlarini (subject-meta-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        python manage.py upload_subjects
        """
        start_time = timezone.now()
        self.stdout.write(
            "HEMIS fan meta-maʼlumotlari sinxronizatsiyasi boshlandi...")

        result = asyncio.run(sync_subjects())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Fan meta-maʼlumotlari muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy fan meta soni: {result['total_subject_metas']}\n"
                f"  Yangi qoʻshilgan fan meta soni: {result['created']}\n"
                f"  Maʼlumoti yangilangan fan meta soni: {result['updated']}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan fan meta soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
