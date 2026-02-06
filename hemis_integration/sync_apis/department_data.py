# university/sync_departments.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from ..models.department import Department
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "name",
    "code",
    "structure_type_name",
    "active",
    # agar kelajakda parent yoki boshqa muhim maydon qo‘shilsa, shu yerga qo‘shing
]


def compute_department_hash(data: dict) -> str:
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
def _save_departments_to_db(all_departments):
    if not all_departments:
        return {
            "total_departments": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        incoming_ids = {d["id"] for d in all_departments}

        # Mavjud bo‘limlarni olish: hash + muhim maydonlar
        fields_to_fetch = ['api_id', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = Department.objects.filter(
            api_id__in=incoming_ids
        ).values(*fields_to_fetch)

        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for d in all_departments:
            api_id = d["id"]

            current_data = {
                "name": d.get("name", "").strip(),
                "code": d.get("code", "").strip(),
                "structure_type_name": d.get("structureType", {}).get("name", "").strip(),
                "active": d.get("active", True),
            }

            # Hash uchun ma'lumot tayyorlash
            hash_data = {
                "name": current_data["name"],
                "code": current_data["code"],
                "structure_type_name": current_data["structure_type_name"],
                "active": current_data["active"],
            }

            new_hash = compute_department_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                # Yangi bo‘lim
                new_obj = Department(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    Department.objects.filter(api_id=api_id).update(
                        self_hash=new_hash,          # yangi hashni saqlash muhim!
                        **current_data
                    )
                    to_update.append(api_id)

        # Yangi bo‘limlarni batch tarzda qo‘shish
        if to_create:
            Department.objects.bulk_create(
                to_create,
                batch_size=300,
                ignore_conflicts=True   # agar duplicate bo'lsa o'tkazib yuborish
            )

        # HEMISdan o‘chirilganlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Department.objects.filter(
                api_id__in=missing_ids
            ).update(active=False)

    return {
        "total_departments": len(all_departments),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_departments():
    url_endpoint = "department-list"

    all_departments = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_departments:
        return {
            "total_departments": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_departments_to_db(all_departments)
    return result
