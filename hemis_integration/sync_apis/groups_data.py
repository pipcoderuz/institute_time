from asgiref.sync import sync_to_async
from django.db import transaction
from ..models.groups import Group
from .api_client import fetch_all_pages


@sync_to_async
def _save_groups_to_db(all_groups):
    """
    Sinxron funksiya: HEMISdan kelgan guruhlarni upsert qilish.
    - Yangi guruhlar → qoʻshiladi
    - Oʻzgargan guruhlar → yangilanadi
    - Oʻchirilgan guruhlar → active=False qilib qoʻyiladi (ixtiyoriy)
    """
    if not all_groups:
        print("Diqqat: Guruhlar roʻyxati boʻsh.")
        return 0

    with transaction.atomic():
        # 1. Kelgan group api_id lar roʻyxati
        incoming_ids = {g["id"] for g in all_groups}

        # 2. Bazadagi mavjud guruhlarni olish (tezlik uchun faqat kerakli maydonlar)
        existing_groups = Group.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'name', 'department_name', 'specialty_name', 'education_lang', 'active'
        )
        existing_map = {eg["api_id"]: eg for eg in existing_groups}

        # Yangi va oʻzgargan guruhlarni tayyorlash
        to_create = []
        to_update = []

        for g in all_groups:
            api_id = g["id"]
            current_data = {
                "name": g["name"],
                "department_name": g["department"]["name"],
                "specialty_name": g["specialty"]["name"],
                "education_lang": g["educationLang"]["name"],
                "active": g["active"],
            }

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi guruh
                to_create.append(Group(api_id=api_id, **current_data))
            else:
                # Oʻzgarganligini tekshirish (hashsiz, oddiy solishtirish)
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    # Oʻzgargan boʻlsa update uchun
                    Group.objects.filter(
                        api_id=api_id).update(**current_data)
                    to_update.append(api_id)

        # 3. Yangi guruhlarni bulk_create bilan qoʻshish
        if to_create:
            Group.objects.bulk_create(to_create)           

        # 5. Ixtiyoriy: API da yoʻq boʻlgan guruhlarni inactive qilish
        # (Agar HEMISdan oʻchirilgan guruhlar boʻlsa, ularni faol emas qilish)
        missing_ids = set(existing_map.keys()) - incoming_ids
        if missing_ids:
            updated = Group.objects.filter(api_id__in=missing_ids).update(active=False)
            
    return {
        "total_groups": len(all_groups),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": len(missing_ids)
        }


async def sync_groups():
    """
    Asosiy funksiya: HEMISdan guruhlarni yuklash va upsert qilish
    """
    url_endpoint = "group-list"

    all_groups = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_groups:
        print("Diqqat: Guruhlar yuklanmadi yoki API boʻsh qaytardi.")
        return 0

    # Bazaga upsert qilish
    saved_count = await _save_groups_to_db(all_groups)

    return saved_count
