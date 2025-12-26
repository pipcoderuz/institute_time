# university/management/commands/upload_departments.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

# sync_departments funksiyasi (upsert va statistika qaytaradi)
from hemis_integration.sync_apis.department_data import sync_departments


class Command(BaseCommand):
    help = "HEMISdan boʻlimlarni (fakultet, kafedra, boʻlim va boshqalar) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        Ishlatish:
        python manage.py upload_departments
        """
        start_time = timezone.now()
        self.stdout.write("HEMIS boʻlimlar sinxronizatsiyasi boshlandi...")

        # Asinxron funksiyani ishga tushirish
        result = asyncio.run(sync_departments())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Boʻlimlar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy boʻlimlar soni: {result['total_departments']}\n"
                f"  Yangi qoʻshilgan boʻlimlar soni: {result['created']}\n"
                f"  Maʼlumoti yangilangan boʻlimlar soni: {result['updated']}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan boʻlimlar soni: {result['deactivated']}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
