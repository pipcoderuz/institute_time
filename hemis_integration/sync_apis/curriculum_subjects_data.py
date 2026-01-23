# university/sync_curriculum_subjects.py

from asgiref.sync import sync_to_async
from django.db import transaction
from datetime import datetime
from ..models.curriculum_subjects import CurriculumSubject
from ..models.curriculum import Curriculum
from ..models.subjects import Subjects
from ..models.department import Department
from .api_client import fetch_all_pages


@sync_to_async
def _save_curriculum_subjects_to_db(all_subjects):
    """
    Upsert + bogʻlanishlar + statistika
    Xato tuzatildi: mavjud boʻlmagan maydonlar olib tashlandi
    """
    if not all_subjects:
        print("Diqqat: Oʻquv rejasi fanlari roʻyxati boʻsh.")
        return {
            "total_subjects": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Bogʻlanishlar uchun maplar
        curriculum_map = {c.api_id: c for c in Curriculum.objects.all()}
        subject_map = {s.api_id: s for s in Subjects.objects.all()}
        department_map = {d.api_id: d for d in Department.objects.all()}

        incoming_ids = {s["id"] for s in all_subjects}

        # Mavjudlarni olish – faqat modelda bor maydonlar
        existing_subjects = CurriculumSubject.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'name', 'code', 'subject_type_name', 'subject_block_name',
            'semester_name', 'credit', 'active'
        )
        existing_map = {es["api_id"]: es for es in existing_subjects}

        to_create = []
        to_update = []

        for s in all_subjects:
            api_id = s["id"]

            # Bogʻlanishlar xavfsiz topish
            curriculum_obj = curriculum_map.get(s.get("_curriculum"))

            subject_data = s.get("subject", {}) or {}
            subject_obj = subject_map.get(subject_data.get("id"))

            department_data = s.get("department")
            department_id = department_data.get("id") if department_data else None
            department_obj = department_map.get(department_id) if department_id else None
            
            # active ni majburiy True/False qilish (null boʻlmaydi!)
            active_value = s.get("active")
            if active_value is None:
                # default qiymat (sizning modelda default=True)
                active_value = True

            current_data = {
                "name": subject_data.get("name", ""),
                "code": subject_data.get("code", ""),
                "subject_type_name": (s.get("subjectType") or {}).get("name", ""),
                "subject_block_name": (s.get("subjectBlock") or {}).get("name", ""),
                "semester_name": (s.get("semester") or {}).get("name", ""),
                "credit": s.get("credit"),
                "active": active_value,
                "created_at": datetime.fromtimestamp(s["created_at"]) if s.get("created_at") else None,
                "updated_at": datetime.fromtimestamp(s["updated_at"]) if s.get("updated_at") else None,
            }

            # department_name ni current_data da saqlamaymiz, chunki modelda yoʻq
            # (agar kerak boʻlsa, modelga qoʻshing yoki department.name dan oling)

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi fan
                new_subject = CurriculumSubject(
                    api_id=api_id,
                    curriculum=curriculum_obj,
                    subject=subject_obj,
                    department=department_obj,
                    **current_data
                )
                to_create.append(new_subject)
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                # Bogʻlanishlar oʻzgarganmi?
                if existing.get('curriculum_id') != (curriculum_obj.id if curriculum_obj else None):
                    changed = True
                if existing.get('subject_id') != (subject_obj.id if subject_obj else None):
                    changed = True
                if existing.get('department_id') != (department_obj.id if department_obj else None):
                    changed = True

                if changed:
                    CurriculumSubject.objects.filter(api_id=api_id).update(
                        curriculum=curriculum_obj,
                        subject=subject_obj,
                        department=department_obj,
                        **current_data
                    )
                    to_update.append(api_id)

        if to_create:
            CurriculumSubject.objects.bulk_create(to_create)

        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = CurriculumSubject.objects.filter(api_id__in=missing_ids).update(active=False)

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

    print(f"API dan {len(all_subjects)} ta fan yuklandi")

    result = await _save_curriculum_subjects_to_db(all_subjects)

    return result
