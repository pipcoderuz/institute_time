# management/commands/upload_curriculums.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

from hemis_integration.sync_apis.curriculum_data import sync_curriculums


class Command(BaseCommand):
    help = "HEMISdan oʻquv rejalarini (curriculum-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        Ishlatish:
        python manage.py upload_curriculums
        """
        start_time = timezone.now()
        self.stdout.write("HEMIS oʻquv rejalar sinxronizatsiyasi boshlandi...")

        result = asyncio.run(sync_curriculums())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Oʻquv rejalar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy oʻquv rejalar soni: {result['total_curriculums']}\n"
                f"  Yangi qoʻshilgan oʻquv rejalar soni: {result['created']}\n"
                f"  Maʼlumoti yangilangan oʻquv rejalar soni: {result['updated']}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan oʻquv rejalar soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
