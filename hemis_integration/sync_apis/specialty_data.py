# university/sync_specialties.py

from asgiref.sync import sync_to_async
from django.db import transaction
from datetime import datetime
from ..models.specialty import Specialty
from .api_client import fetch_all_pages


@sync_to_async
def _save_specialties_to_db(all_specialties):
    """
    Upsert + oʻchirilganlarni inactive qilish + batafsil statistika qaytarish
    (sync_groups va sync_departments ga toʻliq oʻxshash)
    """
    if not all_specialties:
        print("Diqqat: Yoʻnalishlar roʻyxati boʻsh.")
        return {
            "total_specialties": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Kelgan api_id lar
        incoming_ids = {s["id"] for s in all_specialties}

        # Mavjudlarni olish (tezlik uchun)
        existing_specialties = Specialty.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'code', 'name', 'department_name', 'education_type_name', 'active',
            'created_at', 'updated_at'
        )
        existing_map = {es["api_id"]: es for es in existing_specialties}

        to_create = []
        to_update = []

        for s in all_specialties:
            api_id = s["id"]
            department = s.get("department", {})
            education_type = s.get("educationType", {})

            current_data = {
                "code": s["code"],
                "name": s["name"],
                "department_name": department.get("name", ""),
                "education_type_name": education_type.get("name", ""),
                "active": s["active"],
                "created_at": datetime.fromtimestamp(s["created_at"]) if s.get("created_at") else None,
                "updated_at": datetime.fromtimestamp(s["updated_at"]) if s.get("updated_at") else None,
            }

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi yoʻnalish
                to_create.append(Specialty(api_id=api_id, **current_data))
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    Specialty.objects.filter(
                        api_id=api_id).update(**current_data)
                    to_update.append(api_id)

        # Yangi yoʻnalishlarni qoʻshish
        if to_create:
            Specialty.objects.bulk_create(to_create)

        # HEMISdan oʻchirilgan yoʻnalishlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Specialty.objects.filter(
                api_id__in=missing_ids).update(active=False)

        if deactivated_count:
            print(f"Nofaol qilindi: {deactivated_count} ta")

    return {
        "total_specialties": len(all_specialties),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_specialties():
    """
    Asosiy funksiya: specialty-list endpointidan yuklash va upsert
    """
    url_endpoint = "specialty-list"

    all_specialties = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_specialties:
        print("Diqqat: Yoʻnalishlar yuklanmadi yoki API boʻsh qaytardi.")
        return {
            "total_specialties": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_specialties_to_db(all_specialties)

    return result
