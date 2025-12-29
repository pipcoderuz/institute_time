# university/management/commands/upload_auditoriums.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio
from hemis_integration.sync_apis.auditorium_data import sync_auditoriums


class Command(BaseCommand):
    help = "HEMISdan auditoriyalarni (auditorium-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        python manage.py upload_auditoriums
        """
        start_time = timezone.now()
        self.stdout.write("HEMIS auditoriyalar sinxronizatsiyasi boshlandi...")

        result = asyncio.run(sync_auditoriums())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Auditoriyalar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy auditoriyalar soni: {result['total_auditoriums']}\n"
                f"  Yangi qo'shilgan auditoriyalar soni: {result['created']}\n"
                f"  Ma'lumoti yangilangan auditoriyalar soni: {result['updated']}\n"
                f"  HEMIS da o'chirilgani sababli nofaol qilingan auditoriyalar soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )