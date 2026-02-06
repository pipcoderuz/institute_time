# university/sync_curriculum_subjects.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from datetime import datetime
from ..models.curriculum_subjects import CurriculumSubject
from ..models.curriculum import Curriculum
from ..models.subjects import Subjects
from ..models.department import Department
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "name",
    "code",
    "curriculum_id",
    "subject_id",
    "department_id",
    "subject_type_name",
    "subject_block_name",
    "semester_name",
    "credit",
    "active",
    # created_at va updated_at ni hashga kiritmaymiz — ular sinxron vaqt bilan bog‘liq
]


def compute_curriculum_subject_hash(data: dict) -> str:
    """
    Muhim maydonlardan hash hosil qiladi.
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
def _save_curriculum_subjects_to_db(all_subjects):
    if not all_subjects:
        return {
            "total_subjects": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Bog‘lanishlar uchun maplar
        curriculum_map = {c.api_id: c for c in Curriculum.objects.all()}
        subject_map = {s.api_id: s for s in Subjects.objects.all()}
        department_map = {d.api_id: d for d in Department.objects.all()}

        incoming_ids = {s["id"] for s in all_subjects}

        # Mavjudlarni olish – hash + muhim maydonlar
        fields_to_fetch = ['api_id', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = CurriculumSubject.objects.filter(
            api_id__in=incoming_ids
        ).values(*fields_to_fetch)

        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for s in all_subjects:
            api_id = s["id"]

            # Bog‘lanish obyektlari
            curriculum_obj = curriculum_map.get(s.get("_curriculum"))
            subject_obj = subject_map.get(s.get("subject", {}).get("id"))

            department_data = s.get("department")
            department_obj = department_map.get(
                department_data.get("id")) if department_data else None

            current_data = {
                "name": s.get("subject", {}).get("name", "").strip(),
                "code": s.get("subject", {}).get("code", "").strip(),
                "curriculum": curriculum_obj,
                "subject": subject_obj,
                "department": department_obj,
                "subject_type_name": (s.get("subjectType") or {}).get("name", "").strip(),
                "subject_block_name": (s.get("subjectBlock") or {}).get("name", "").strip(),
                "semester_name": (s.get("semester") or {}).get("name", "").strip(),
                "credit": s.get("credit"),
                "active": bool(s.get("active", True)),
                "created_at": datetime.fromtimestamp(s["created_at"]) if s.get("created_at") else None,
                "updated_at": datetime.fromtimestamp(s["updated_at"]) if s.get("updated_at") else None,
            }

            # Hash uchun ma'lumot (id lar ishlatiladi)
            hash_data = {
                "name": current_data["name"],
                "code": current_data["code"],
                "curriculum_id": curriculum_obj.api_id if curriculum_obj else None,
                "subject_id": subject_obj.api_id if subject_obj else None,
                "department_id": department_obj.api_id if department_obj else None,
                "subject_type_name": current_data["subject_type_name"],
                "subject_block_name": current_data["subject_block_name"],
                "semester_name": current_data["semester_name"],
                "credit": current_data["credit"],
                "active": current_data["active"],
            }

            new_hash = compute_curriculum_subject_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                # Yangi yozuv
                new_obj = CurriculumSubject(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                # Hash farq qilsa → update
                if existing_rec["self_hash"] != new_hash:
                    CurriculumSubject.objects.filter(api_id=api_id).update(
                        self_hash=new_hash,          # yangi hashni saqlash shart!
                        **current_data
                    )
                    to_update.append(api_id)

        # Yangi yozuvlarni batchda qo‘shish
        if to_create:
            CurriculumSubject.objects.bulk_create(
                to_create,
                batch_size=300,
                ignore_conflicts=True
            )

        # Yo‘qolganlarni inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = CurriculumSubject.objects.filter(
                api_id__in=missing_ids
            ).update(active=False)

    return {
        "total_subjects": len(all_subjects),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_curriculum_subjects():
    url_endpoint = "curriculum-subject-list"

    all_subjects = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_subjects:
        return {
            "total_subjects": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_curriculum_subjects_to_db(all_subjects)
    return result
