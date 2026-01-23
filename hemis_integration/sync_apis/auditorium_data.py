# university/sync_auditoriums.py

from asgiref.sync import sync_to_async
from django.db import transaction
from ..models.auditorium import Auditorium
from .api_client import fetch_all_pages


@sync_to_async
def _save_auditoriums_to_db(all_auditoriums):
    """
    Upsert + oʻchirilganlarni inactive qilish + batafsil statistika qaytarish
    (sync_departments.py bilan bir xil logika)
    """
    if not all_auditoriums:
        return {
            "total_auditoriums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Kelgan code lar (unique maydon)
        incoming_codes = {a["code"] for a in all_auditoriums}

        # Mavjudlarni olish (tezlik uchun)
        existing_auditoriums = Auditorium.objects.filter(code__in=incoming_codes).values(
            'code', 'name', 'auditorium_type_name', 'building_name', 'volume', 'active'
        )
        existing_map = {ea["code"]: ea for ea in existing_auditoriums}

        to_create = []
        to_update = []

        for a in all_auditoriums:
            code = a["code"]
            auditorium_type = a.get("auditoriumType", {})
            building = a.get("building", {})

            current_data = {
                "name": a["name"],
                "auditorium_type_name": auditorium_type.get("name", ""),
                "building_name": building.get("name", ""),
                "volume": a["volume"],
                "active": a["active"],
            }

            existing = existing_map.get(code)

            if not existing:
                # Yangi auditoriya
                to_create.append(Auditorium(code=code, **current_data))
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    Auditorium.objects.filter(code=code).update(**current_data)
                    to_update.append(code)

        # Yangi auditoriyalarni qoʻshish
        if to_create:
            Auditorium.objects.bulk_create(to_create)


        # HEMISdan oʻchirilgan auditoriyalarni inactive qilish
        missing_codes = set(existing_map.keys()) - incoming_codes
        deactivated_count = 0
        if missing_codes:
            deactivated_count = Auditorium.objects.filter(
                code__in=missing_codes).update(active=False)

    return {
        "total_auditoriums": len(all_auditoriums),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_auditoriums():
    """
    Asosiy funksiya: auditorium-list endpointidan yuklash va upsert
    """
    url_endpoint = "auditorium-list"

    all_auditoriums = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_auditoriums:
        return {
            "total_auditoriums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_auditoriums_to_db(all_auditoriums)

    return result
