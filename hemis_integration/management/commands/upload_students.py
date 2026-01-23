# university/management/commands/upload_students.py

from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio
from hemis_integration.sync_apis.student_data import sync_students


class Command(BaseCommand):
    help = "HEMISdan talabalarni (student-list) tez va xavfsiz sinxronizatsiya qilish"

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write("HEMIS talabalar sinxronizatsiyasi boshlandi... (bu biroz vaqt olishi mumkin)")

        result = asyncio.run(sync_students())

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Talabalar muvaffaqiyatli sinxronizatsiya qilindi!\n"
                f"  Yuklangan umumiy talabalar soni: {result['total_students']:,}\n"
                f"  Yangi qoʻshilgan talabalar soni: {result['created']:,}\n"
                f"  Maʼlumoti yangilangan talabalar soni (hash oʻzgargan): {result['updated']:,}\n"
                f"  HEMISda oʻchirilgani sababli nofaol qilingan talabalar soni: {result['deactivated']:,}\n"
                f"  Umumiy vaqt: {duration:.2f} sekund"
            )
        )
