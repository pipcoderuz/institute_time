# university/sync_curriculums.py

from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from ..models.curriculum import Curriculum
from ..models.specialty import Specialty
from ..models.department import Department
from .api_client import fetch_all_pages


IMPORTANT_FIELDS_FOR_HASH = [
    "name",
    "specialty_id",          # yangi FK
    "department_id",         # yangi FK
    "education_year_name",
    "education_year_current",
    "education_type_name",
    "education_form_name",
    "marking_system_name",
    "marking_minimum_limit",
    "marking_gpa_limit",
    "semester_count",
    "education_period",
    "accepted",
    "active",
]


def compute_curriculum_hash(data: dict) -> str:
    """Muhim fieldlardan hash hosil qiladi"""
    parts = []
    for field in IMPORTANT_FIELDS_FOR_HASH:
        value = data.get(field)
        if value is None:
            parts.append("")
        elif isinstance(value, (float, int)):
            parts.append(str(value))
        else:
            parts.append(str(value))
    raw = "|".join(parts)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


@sync_to_async
def _save_curriculums_to_db(all_curriculums):
    if not all_curriculums:
        return {
            "total_curriculums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Maplar
        specialty_map = {s.api_id: s for s in Specialty.objects.all()}
        department_map = {d.api_id: d for d in Department.objects.all()}

        incoming_ids = {c["id"] for c in all_curriculums}

        # Mavjudlarni olish – hash + muhim fieldlar
        fields_to_fetch = ['api_id', 'self_hash'] + IMPORTANT_FIELDS_FOR_HASH
        existing = Curriculum.objects.filter(
            api_id__in=incoming_ids).values(*fields_to_fetch)
        existing_map = {e["api_id"]: e for e in existing}

        to_create = []
        to_update = []

        for c in all_curriculums:
            api_id = c["id"]

            specialty_obj = specialty_map.get(c.get("specialty", {}).get("id"))
            department_obj = department_map.get(c.get("department", {}).get("id"))

            education_year = c.get("educationYear", {})
            education_type = c.get("educationType", {})
            education_form = c.get("educationForm", {})
            marking = c.get("markingSystem", {})

            current_data = {
                "name": c.get("name", ""),
                "specialty": specialty_obj,
                "department": department_obj,
                "education_year_name": education_year.get("name", ""),
                "education_year_current": education_year.get("current", False),
                "education_type_name": education_type.get("name", ""),
                "education_form_name": education_form.get("name", ""),
                "marking_system_name": marking.get("name", ""),
                "marking_minimum_limit": marking.get("minimum_limit"),
                "marking_gpa_limit": marking.get("gpa_limit"),
                "semester_count": c.get("semester_count"),
                "education_period": c.get("education_period"),
                "accepted": c.get("accepted", False),
                "active": c.get("active", True),
            }

            # Hash uchun ma'lumot tayyorlash
            hash_data = {
                "name": current_data["name"],
                "specialty_id": specialty_obj.api_id if specialty_obj else None,
                "department_id": department_obj.api_id if department_obj else None,
                "education_year_name": current_data["education_year_name"],
                "education_year_current": current_data["education_year_current"],
                "education_type_name": current_data["education_type_name"],
                "education_form_name": current_data["education_form_name"],
                "marking_system_name": current_data["marking_system_name"],
                "marking_minimum_limit": current_data["marking_minimum_limit"],
                "marking_gpa_limit": current_data["marking_gpa_limit"],
                "semester_count": current_data["semester_count"],
                "education_period": current_data["education_period"],
                "accepted": current_data["accepted"],
                "active": current_data["active"],
            }

            new_hash = compute_curriculum_hash(hash_data)

            existing_rec = existing_map.get(api_id)

            if not existing_rec:
                new_obj = Curriculum(
                    api_id=api_id,
                    self_hash=new_hash,
                    **current_data
                )
                to_create.append(new_obj)
            else:
                if existing_rec["self_hash"] != new_hash:
                    # Yangi hashni ham saqlaymiz!
                    Curriculum.objects.filter(api_id=api_id).update(
                        self_hash=new_hash, **current_data)
                    to_update.append(api_id)

        # Bulk create
        if to_create:
            Curriculum.objects.bulk_create(to_create, batch_size=300)

        # Deactivated
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Curriculum.objects.filter(
                api_id__in=missing_ids).update(active=False)

    return {
        "total_curriculums": len(all_curriculums),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_curriculums():
    url_endpoint = "curriculum-list"

    all_curriculums = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_curriculums:
        return {
            "total_curriculums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_curriculums_to_db(all_curriculums)
    return result
