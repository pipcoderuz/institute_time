# university/sync_specialties.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from datetime import datetime
from ..models.specialty import Specialty
from ..models.department import Department
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "code",
    "name",
    "department_id",           # department.api_id
    "education_type_name",
    "active",
    # created_at va updated_at ni hashga kiritmaymiz — ular sinxron vaqt bilan bog'liq
    # agar kerak bo'lsa qo'shishingiz mumkin, lekin odatda kerak emas
]


def compute_specialty_hash(data: dict) -> str:
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
def _save_specialties_to_db(all_specialties):
    if not all_specialties:
        return {
            "total_specialties": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Map: department api_id → obyekt
        department_map = {d.api_id: d for d in Department.objects.all()}

        incoming_ids = {s["id"] for s in all_specialties}

        # Mavjudlarni olish: hash + muhim maydonlar
        fields_to_fetch = ['api_id', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = Specialty.objects.filter(
            api_id__in=incoming_ids
        ).values(*fields_to_fetch)

        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for s in all_specialties:
            api_id = s["id"]

            # ForeignKey bog'lanish
            department_obj = department_map.get(
                s.get("department", {}).get("id"))

            current_data = {
                "code": s.get("code", "").strip(),
                "name": s.get("name", "").strip(),
                "department": department_obj,
                "education_type_name": s.get("educationType", {}).get("name", "").strip(),
                "active": s.get("active", True),
                "created_at": datetime.fromtimestamp(s["created_at"]) if s.get("created_at") else None,
                "updated_at": datetime.fromtimestamp(s["updated_at"]) if s.get("updated_at") else None,
            }

            # Hash uchun ma'lumot (faqat muhim fieldlar + id)
            hash_data = {
                "code": current_data["code"],
                "name": current_data["name"],
                "department_id": department_obj.api_id if department_obj else None,
                "education_type_name": current_data["education_type_name"],
                "active": current_data["active"],
            }

            new_hash = compute_specialty_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                # Yangi yo'nalish
                new_obj = Specialty(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    Specialty.objects.filter(api_id=api_id).update(
                        self_hash=new_hash,          # yangi hashni saqlash muhim!
                        **current_data
                    )
                    to_update.append(api_id)

        # Yangi yo'nalishlarni batch tarzda qo'shish
        if to_create:
            Specialty.objects.bulk_create(
                to_create,
                batch_size=300,
                ignore_conflicts=True   # duplicate api_id bo'lsa xato chiqmasin
            )

        # HEMISdan o'chirilganlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Specialty.objects.filter(
                api_id__in=missing_ids
            ).update(active=False)

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
        return {
            "total_specialties": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_specialties_to_db(all_specialties)
    return result
