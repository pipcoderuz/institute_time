# management/commands/upload_specialties.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

from hemis_integration.sync_apis.specialty_data import sync_specialties


class Command(BaseCommand):
    help = "HEMISdan yoʻnalishlarni (specialty-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        Ishlatish:
        python manage.py upload_specialties
        """
        start_time = timezone.now()
        self.stdout.write("HEMIS yoʻnalishlar sinxronizatsiyasi boshlandi...")

        result = asyncio.run(sync_specialties())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Yoʻnalishlar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy yoʻnalishlar soni: {result['total_specialties']}\n"
                f"  Yangi qoʻshilgan yoʻnalishlar soni: {result['created']}\n"
                f"  Maʼlumoti yangilangan yoʻnalishlar soni: {result['updated']}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan yoʻnalishlar soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
