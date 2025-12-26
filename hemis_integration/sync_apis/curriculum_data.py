# university/sync_curriculums.py

from asgiref.sync import sync_to_async
from django.db import transaction
from ..models.curriculum import Curriculum
from .api_client import fetch_all_pages


@sync_to_async
def _save_curriculums_to_db(all_curriculums):
    """
    Upsert + oʻchirilganlarni inactive qilish + batafsil statistika qaytarish
    (sync_groups, sync_departments, sync_specialties ga toʻliq oʻxshash)
    """
    if not all_curriculums:
        print("Diqqat: Oʻquv rejalar roʻyxati boʻsh.")
        return {
            "total_curriculums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    with transaction.atomic():
        # Kelgan api_id lar
        incoming_ids = {c["id"] for c in all_curriculums}

        # Mavjudlarni olish (tezlik uchun)
        existing_curriculums = Curriculum.objects.filter(api_id__in=incoming_ids).values(
            'api_id', 'name', 'specialty_name', 'department_name',
            'education_year_name', 'education_year_current',
            'education_type_name', 'education_form_name',
            'marking_system_name', 'marking_minimum_limit', 'marking_gpa_limit',
            'semester_count', 'education_period', 'accepted', 'active'
        )
        existing_map = {ec["api_id"]: ec for ec in existing_curriculums}

        to_create = []
        to_update = []

        for c in all_curriculums:
            api_id = c["id"]
            specialty = c.get("specialty", {})
            department = c.get("department", {})
            education_year = c.get("educationYear", {})
            education_type = c.get("educationType", {})
            education_form = c.get("educationForm", {})
            marking_system = c.get("markingSystem", {})

            current_data = {
                "name": c["name"],
                "specialty_name": specialty.get("name", ""),
                "department_name": department.get("name", ""),
                "education_year_name": education_year.get("name", ""),
                "education_year_current": education_year.get("current", False),
                "education_type_name": education_type.get("name", ""),
                "education_form_name": education_form.get("name", ""),
                "marking_system_name": marking_system.get("name", ""),
                "marking_minimum_limit": marking_system.get("minimum_limit"),
                "marking_gpa_limit": marking_system.get("gpa_limit"),
                "semester_count": c["semester_count"],
                "education_period": c["education_period"],
                "accepted": c["accepted"],
                "active": c["active"],
            }

            existing = existing_map.get(api_id)

            if not existing:
                # Yangi oʻquv rejasi
                to_create.append(Curriculum(api_id=api_id, **current_data))
            else:
                # Oʻzgarganligini tekshirish
                changed = False
                for key, value in current_data.items():
                    if existing[key] != value:
                        changed = True
                        break

                if changed:
                    Curriculum.objects.filter(
                        api_id=api_id).update(**current_data)
                    to_update.append(api_id)

        # Yangi oʻquv rejalarini qoʻshish
        if to_create:
            Curriculum.objects.bulk_create(to_create)

        # HEMISdan oʻchirilgan oʻquv rejalarini inactive qilish
        missing_ids = set(existing_map.keys()) - incoming_ids
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Curriculum.objects.filter(
                api_id__in=missing_ids).update(active=False)


        if deactivated_count:
            print(f"Nofaol qilindi: {deactivated_count} ta")

    return {
        "total_curriculums": len(all_curriculums),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_curriculums():
    """
    Asosiy funksiya: curriculum-list endpointidan yuklash va upsert
    """
    url_endpoint = "curriculum-list"

    all_curriculums = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_curriculums:
        print("Diqqat: Oʻquv rejalar yuklanmadi yoki API boʻsh qaytardi.")
        return {
            "total_curriculums": 0,
            "created": 0,
            "updated": 0,
            "deactivated": 0
        }

    result = await _save_curriculums_to_db(all_curriculums)

    return result
