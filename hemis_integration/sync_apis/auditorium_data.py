# university/sync_auditoriums.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from ..models.auditorium import Auditorium
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "name",
    "auditorium_type_name",
    "building_name",
    "volume",
    "active",
    # agar kelajakda qo'shimcha maydonlar paydo bo'lsa, shu yerga qo'shing
]


def compute_auditorium_hash(data: dict) -> str:
    """
    Muhim maydonlardan hash hosil qiladi.
    Oddiy string birlashtirish + MD5.
    """
    parts = []
    for field in IMPORTANT_FIELDS_FOR_HASH:
        value = data.get(field)
        if value is None:
            parts.append("")
        elif isinstance(value, (int, float, bool)):
            parts.append(str(value))
        else:
            parts.append(str(value).strip())

    raw_string = "|".join(parts)
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()


@sync_to_async
def _save_auditoriums_to_db(all_auditoriums):
    if not all_auditoriums:
        return {
            "total_auditoriums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # API dan kelgan code larni majburan string + strip qilamiz
        incoming_codes = {str(a.get("code", "")).strip()
                          for a in all_auditoriums if a.get("code")}

        # Mavjud auditoriyalarni olish (hash + muhim maydonlar)
        fields_to_fetch = ['code', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = Auditorium.objects.filter(
            code__in=incoming_codes
        ).values(*fields_to_fetch)

        # DB dagi code larni ham str + strip
        existing_map = {str(e["code"]).strip(): e for e in existing}

        to_create = []
        to_update = []

        for a in all_auditoriums:
            code = str(a.get("code", "")).strip()  # Majburan string + strip

            auditorium_type = a.get("auditoriumType", {})
            building = a.get("building", {})

            current_data = {
                "name": a.get("name", "").strip(),
                "auditorium_type_name": auditorium_type.get("name", "").strip(),
                "building_name": building.get("name", "").strip(),
                "volume": a.get("volume"),
                "active": a.get("active", True),
            }

            # Hash uchun ma'lumot
            hash_data = {
                "name": current_data["name"],
                "auditorium_type_name": current_data["auditorium_type_name"],
                "building_name": current_data["building_name"],
                "volume": current_data["volume"],
                "active": current_data["active"],
            }

            new_hash = compute_auditorium_hash(hash_data)

            existing_rec = existing_map.get(code)

            if not existing_rec:
                # Yangi auditoriya
                new_obj = Auditorium(
                    code=code,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    Auditorium.objects.filter(code=code).update(
                        self_hash=new_hash,          # yangi hashni saqlash shart!
                        **current_data
                    )
                    to_update.append(code)

        # Yangi yozuvlarni batch tarzda qo'shish
        if to_create:
            Auditorium.objects.bulk_create(
                to_create, batch_size=300, ignore_conflicts=True)

        # O'chirilganlarni inactive qilish
        missing_codes = set(existing_map.keys()) - incoming_codes
        deactivated_count = 0
        if missing_codes:
            deactivated_count = Auditorium.objects.filter(
                code__in=missing_codes
            ).update(active=False)

    return {
        "total_auditoriums": len(all_auditoriums),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_auditoriums():
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
