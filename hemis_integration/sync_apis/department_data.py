# university/sync_departments.py

from asgiref.sync import sync_to_async
from django.db import transaction
from ..models.department import Department
from .api_client import fetch_all_pages


@sync_to_async
def _save_departments_to_db(all_departments):
    """
    Upsert + oʻchirilganlarni inactive qilish + batafsil statistika qaytarish
    """
    if not all_departments:
        print("Diqqat: Boʻlimlar roʻyxati boʻsh.")
        return {
            "total_departments": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Kelgan api_id lar
        incoming_ids = {d["id"] for d in all_departments}

        # Mavjudlarni olish (tezlik uchun)
        existing_departments = Department.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'name', 'code', 'structure_type_name', 'active'
        )
        existing_map = {ed["api_id"]: ed for ed in existing_departments}

        to_create = []
        to_update = []

        for d in all_departments:
            api_id = d["id"]
            current_data = {
                "name": d["name"],
                "code": d["code"],
                "structure_type_name": d["structureType"].get("name", ""),
                "active": d["active"],
            }

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi
                to_create.append(Department(api_id=api_id, **current_data))
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    Department.objects.filter(
                        api_id=api_id).update(**current_data)
                    to_update.append(api_id)

        # Yangi boʻlimlarni qoʻshish
        if to_create:
            Department.objects.bulk_create(to_create)

        # HEMISdan oʻchirilganlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Department.objects.filter(
                api_id__in=missing_ids).update(active=False)

        if deactivated_count:
            print(f"Nofaol qilindi: {deactivated_count} ta")

    return {
        "total_departments": len(all_departments),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_departments():
    """
    Asosiy funksiya: department-list dan yuklash va upsert
    """
    url_endpoint = "department-list"

    all_departments = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_departments:
        print("Diqqat: Boʻlimlar yuklanmadi yoki API boʻsh qaytardi.")
        return {
            "total_departments": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    print(f"API dan {len(all_departments)} ta boʻlim yuklandi")

    result = await _save_departments_to_db(all_departments)

    return result
