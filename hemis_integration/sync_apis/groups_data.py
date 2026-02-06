# university/sync_groups.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from ..models.groups import Group
from ..models.specialty import Specialty
from ..models.department import Department
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "name",
    "department_id",         # department.api_id
    "specialty_id",          # specialty.api_id
    "education_lang",
    "active",
    # agar kelajakda level, course yoki boshqa muhim maydonlar qo'shilsa, shu yerga qo'shing
]


def compute_group_hash(data: dict) -> str:
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
def _save_groups_to_db(all_groups):
    if not all_groups:
        return {
            "total_groups": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Maplar (tezroq bog'lanish uchun)
        department_map = {d.api_id: d for d in Department.objects.all()}
        specialty_map = {s.api_id: s for s in Specialty.objects.all()}

        incoming_ids = {g["id"] for g in all_groups}

        # Mavjud guruhlarni olish: hash + muhim maydonlar
        fields_to_fetch = ['api_id', 'self_hash'] + [
            f if f not in ("department_id", "specialty_id") else f for f in IMPORTANT_FIELDS_FOR_HASH
        ]
        existing = Group.objects.filter(
            api_id__in=incoming_ids
        ).values(*fields_to_fetch)

        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for g in all_groups:
            api_id = g["id"]

            # ForeignKey obyektlarini topish
            department_obj = department_map.get(
                g.get("department", {}).get("id"))
            specialty_obj = specialty_map.get(g.get("specialty", {}).get("id"))

            current_data = {
                "name": g.get("name", "").strip(),
                "department": department_obj,
                "specialty": specialty_obj,
                "education_lang": g.get("educationLang", {}).get("name", "").strip(),
                "active": g.get("active", True),
            }

            # Hash uchun ma'lumot tayyorlash (id lar ishlatiladi)
            hash_data = {
                "name": current_data["name"],
                "department_id": department_obj.api_id if department_obj else None,
                "specialty_id": specialty_obj.api_id if specialty_obj else None,
                "education_lang": current_data["education_lang"],
                "active": current_data["active"],
            }

            new_hash = compute_group_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                # Yangi guruh
                new_obj = Group(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    Group.objects.filter(api_id=api_id).update(
                        self_hash=new_hash,          # yangi hashni saqlash muhim!
                        **current_data
                    )
                    to_update.append(api_id)

        # Yangi guruhlarni batch tarzda qo'shish
        if to_create:
            Group.objects.bulk_create(
                to_create,
                batch_size=300,
                ignore_conflicts=True   # duplicate api_id bo'lsa o'tkazib yuborish
            )

        # HEMISdan o'chirilgan guruhlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Group.objects.filter(
                api_id__in=missing_ids
            ).update(active=False)

    return {
        "total_groups": len(all_groups),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_groups():
    """
    Asosiy funksiya: group-list endpointidan yuklash va upsert
    """
    url_endpoint = "group-list"

    all_groups = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_groups:
        return {
            "total_groups": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_groups_to_db(all_groups)
    return result
