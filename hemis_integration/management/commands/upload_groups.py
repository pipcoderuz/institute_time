# university/management/commands/sync_groups.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

# api_client bilan ishlaydigan funksiya
from hemis_integration.sync_apis.groups_data import sync_groups


class Command(BaseCommand):
    help = "HEMISdan faqat guruhlarni tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        """
        python manage.py sync_groups
        """
        start_time = timezone.now()
        self.stdout.write("HEMIS guruhlar sinxronizatsiyasi boshlandi...")

        # Asinxron funksiyani ishga tushirish
        result = asyncio.run(sync_groups())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Guruhlar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy guruhlar soni: {result["total_groups"]}\n"
                f"  Yangi qo'shilgan guruhlar soni: {result["created"]}\n"
                f"  Ma'lumoti yangilangan guruhlar soni: {result["updated"]}\n"
                f"  HEMIS da o'chirilgani sababli nofaol qilingan guruhlar soni: {result["deactivated"]}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
