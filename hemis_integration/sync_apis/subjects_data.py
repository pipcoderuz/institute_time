# university/sync_subject_metas.py

from asgiref.sync import sync_to_async
from django.db import transaction
from ..models.subjects import Subjects
from .api_client import fetch_all_pages


@sync_to_async
def _save_subject_metas_to_db(all_subject_metas):
    """
    Upsert + oʻchirilganlarni inactive qilish + batafsil statistika qaytarish
    (sync_departments.py bilan bir xil logika)
    """
    if not all_subject_metas:
        return {
            "total_subject_metas": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Kelgan api_id lar
        incoming_ids = {s["id"] for s in all_subject_metas}

        # Mavjudlarni olish (tezlik uchun)
        existing_metas = Subjects.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'code', 'name', 'subject_group_name', 'education_type_name', 'active'
        )
        existing_map = {em["api_id"]: em for em in existing_metas}

        to_create = []
        to_update = []

        for s in all_subject_metas:
            api_id = s["id"]
            subject_group = s.get("subjectGroup", {})
            education_type = s.get("educationType", {})

            current_data = {
                "code": s["code"],
                "name": s["name"],
                "subject_group_name": subject_group.get("name", ""),
                "education_type_name": education_type.get("name", ""),
                "active": s["active"],
            }

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi fan meta
                to_create.append(Subjects(api_id=api_id, **current_data))
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    Subjects.objects.filter(api_id=api_id).update(**current_data)
                    to_update.append(api_id)

        # Yangi fan meta-maʼlumotlarini qoʻshish
        if to_create:
            Subjects.objects.bulk_create(to_create)

        # HEMISdan oʻchirilgan fan meta-maʼlumotlarini inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Subjects.objects.filter(
                api_id__in=missing_ids).update(active=False)

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
