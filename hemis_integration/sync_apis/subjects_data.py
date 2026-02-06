# university/sync_subjects.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from ..models.subjects import Subjects
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "code",
    "name",
    "subject_group_name",
    "education_type_name",
    "active",
    # agar kelajakda qo'shimcha muhim maydonlar (masalan credit, semester) paydo bo'lsa, shu yerga qo'shing
]


def compute_subject_meta_hash(data: dict) -> str:
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
def _save_subject_metas_to_db(all_subject_metas):
    if not all_subject_metas:
        return {
            "total_subject_metas": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        

        # Mavjudlarni olish – hash + muhim fieldlar
        incoming_ids = {c["id"] for c in all_subject_metas}

        # Mavjud subject meta'larni olish: hash + muhim maydonlar
        fields_to_fetch = ['api_id', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = Subjects.objects.filter(
            api_id__in=incoming_ids).values(*fields_to_fetch)

        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for s in all_subject_metas:
            api_id = s.get("id")
            if not api_id:
                continue  # agar id bo'lmasa o'tkazib yuboramiz

            subject_group = s.get("subjectGroup", {})
            education_type = s.get("educationType", {})

            current_data = {
                "code": s.get("code", "").strip(),
                "name": s.get("name", "").strip(),
                "subject_group_name": subject_group.get("name", "").strip(),
                "education_type_name": education_type.get("name", "").strip(),
                "active": s.get("active", True),
            }

            # Hash uchun ma'lumot tayyorlash
            hash_data = {
                "code": current_data["code"],
                "name": current_data["name"],
                "subject_group_name": current_data["subject_group_name"],
                "education_type_name": current_data["education_type_name"],
                "active": current_data["active"],
            }

            new_hash = compute_subject_meta_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                # Yangi subject meta
                new_obj = Subjects(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    Subjects.objects.filter(api_id=api_id).update(
                        self_hash=new_hash,
                        name=current_data["name"],
                        subject_group_name=current_data["subject_group_name"],
                        education_type_name=current_data["education_type_name"],
                        active=current_data["active"],
                    )
                    to_update.append(api_id)

        # Yangi yozuvlarni batch tarzda qo'shish
        if to_create:
            Subjects.objects.bulk_create(
                to_create,
                batch_size=300,
                ignore_conflicts=True   # duplicate api_id bo'lsa xato chiqmasin
            )

        # HEMISdan o'chirilganlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Subjects.objects.filter(
                api_id__in=missing_ids
            ).update(active=False)

    return {
        "total_subject_metas": len(all_subject_metas),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_subjects():
    """
    Asosiy funksiya: subject-meta-list endpointidan yuklash va upsert
    """
    url_endpoint = "subject-meta-list"

    all_subject_metas = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_subject_metas:
        return {
            "total_subject_metas": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_subject_metas_to_db(all_subject_metas)
    return result
