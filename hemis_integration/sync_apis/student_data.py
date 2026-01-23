from asgiref.sync import sync_to_async
import hashlib
from django.db import transaction
from datetime import datetime
from django.utils import timezone
from ..models.student import Student
from ..models.groups import Group
from ..models.specialty import Specialty
from ..models.curriculum import Curriculum
from ..models.department import Department
from accounts.models import CustomUser
from .api_client import fetch_all_pages

IMPORTANT_FIELDS = [
    "full_name",
    "group",           # → group.id
    "specialty",       # → specialty.id
    "curriculum",      # → curriculum.id
    "department",      # → department.id
    "student_status_name",
    "education_form_name",
    "education_type_name",
    "payment_form_name",
    "student_type_name",
    "avg_gpa",
    "year_of_enter",
    "education_year_name",
    "level_name",
    "hemis_student_id_number"
]


def compute_self_created_hash_value(student_data: dict) -> str:
    parts = []
    for field in IMPORTANT_FIELDS:
        value = student_data.get(field)

        if value is None:
            parts.append("")
        elif isinstance(value, float):
            # Eng muhim qism: floatni 2 kasr bilan string qilamiz
            parts.append(f"{value:.2f}")
        elif isinstance(value, (int, str, bool)):
            parts.append(str(value))
        else:
            # boshqa tiplar uchun (masalan date emas, lekin ehtiyot chorasi)
            parts.append(str(value))

    raw_string = "|".join(parts)
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()



@sync_to_async
def _save_students_to_db(all_students):
    if not all_students:
        return {"total_students": 0, "created": 0, "updated": 0, "deactivated": 0}

    with transaction.atomic():
        group_map = {g.api_id: g for g in Group.objects.all()}
        specialty_map = {s.api_id: s for s in Specialty.objects.all()}
        curriculum_map = {c.api_id: c for c in Curriculum.objects.all()}
        department_map = {d.api_id: d for d in Department.objects.all()}

        incoming_ids = {s["id"] for s in all_students}

        # Faqat kerakli fieldlarni olamiz
        fields_to_fetch = ['api_id', 'self_created_hash_value'] + [
            f if f not in ("group", "specialty", "curriculum", "department")
            else f + "_id" for f in IMPORTANT_FIELDS
        ]
        # Agar modelda group_id, specialty_id kabi ForeignKey bo‘lsa
        # values() ga _id qo‘shiladi

        existing_students = Student.objects.filter(api_id__in=incoming_ids).values(
            *set(fields_to_fetch)  # duplicate'larni olib tashlaydi
        )
        existing_map = {es["api_id"]: es for es in existing_students}

        to_create = []
        to_update = []

        # Yangi talabalar uchun user yaratish (oldingi kod bilan bir xil)
        new_student_id_numbers = {}
        for s in all_students:
            sid = s.get("student_id_number")
            if sid:
                new_student_id_numbers[s["id"]] = sid

        existing_usernames = set(CustomUser.objects.filter(
            username__in=new_student_id_numbers.values()
        ).values_list('username', flat=True))

        for api_id, sid in new_student_id_numbers.items():
            if sid not in existing_usernames:
                user = CustomUser.objects.create(
                    username=sid,
                    first_name=s.get("first_name", ""),
                    last_name=s.get("second_name", ""),
                    email=s.get("email", f"{sid}@student.uz"),
                )
                user.set_password(sid)
                user.add_role('student')
                user.set_active_role('student')
                user.save()

        # Asosiy sikl
        for s in all_students:
            api_id = s["id"]
            group_id = s.get("group", {}).get("id")
            specialty_id = s.get("specialty", {}).get("id")
            curriculum_id = s.get("_curriculum")
            department_id = s.get("department", {}).get("id")

            group_obj = group_map.get(group_id)
            specialty_obj = specialty_map.get(specialty_id)
            curriculum_obj = curriculum_map.get(curriculum_id)
            department_obj = department_map.get(department_id)
            
            current_data = {
                "full_name": s["full_name"],
                "short_name": s.get("short_name", ""),
                "first_name": s["first_name"],
                "second_name": s["second_name"],
                "third_name": s.get("third_name", ""),
                "hemis_student_id_number": s.get("student_id_number"),
                "birth_date": datetime.fromtimestamp(s["birth_date"]).date() if s.get("birth_date") else None,
                "gender": s.get("gender", {}).get("name", ""),
                "image": s["image"],
                "image_full": s["image_full"],
                "country_name": s.get("country", {}).get("name", ""),
                "province_name": s.get("province", {}).get("name", ""),
                "district_name": s.get("district", {}).get("name", ""),
                "citizenship_name": s.get("citizenship", {}).get("name", ""),
                "level_name": s.get("level", {}).get("name", ""),
                "education_year_name": s.get("educationYear", {}).get("name", ""),
                "year_of_enter": s.get("year_of_enter"),
                "avg_gpa": s["avg_gpa"],
                "avg_grade": s["avg_grade"],
                "total_credit": s["total_credit"],
                "student_status_name": s.get("studentStatus", {}).get("name", ""),
                "education_form_name": s.get("educationForm", {}).get("name", ""),
                "education_type_name": s.get("educationType", {}).get("name", ""),
                "payment_form_name": s.get("paymentForm", {}).get("name", ""),
                "student_type_name": s.get("studentType", {}).get("name", ""),
                "active": s.get("active", True),
                "updated_at_api": datetime.fromtimestamp(s["updated_at"]) if s.get("updated_at") else None,
                "last_synced_at": timezone.now(),
            }

            hash_data = {
                "group": group_id,
                "specialty": specialty_id,
                "curriculum": curriculum_id,
                "department": department_id,
                **{k: v for k, v in current_data.items() if k in IMPORTANT_FIELDS}
            }
            new_hash = compute_self_created_hash_value(hash_data)
            existing = existing_map.get(api_id)

            if not existing:
                new_student = Student(
                    api_id=api_id,
                    group=group_obj,
                    specialty=specialty_obj,
                    curriculum=curriculum_obj,
                    department=department_obj,
                    self_created_hash_value=new_hash,
                    **current_data
                )
                to_create.append(new_student)
            else:                
                if existing["self_created_hash_value"] != new_hash:
                    Student.objects.filter(api_id=api_id).update(
                        group=group_obj,
                        specialty=specialty_obj,
                        curriculum=curriculum_obj,
                        department=department_obj,
                        self_created_hash_value=new_hash,
                        **current_data
                    )
                    to_update.append(api_id)

        if to_create:
            Student.objects.bulk_create(to_create, batch_size=500)

            # Yangi yaratilganlarga user bog‘lash
            for student in to_create:
                sid = student.hemis_student_id_number
                if sid:
                    try:
                        user = CustomUser.objects.get(username=sid)
                        Student.objects.filter(id=student.id).update(user=user)
                    except CustomUser.DoesNotExist:
                        pass

        # Deactivated
        missing_ids = set(existing_map.keys()) - incoming_ids
        print("Deactivating students with IDs:", len(missing_ids),len(incoming_ids), len(existing_map.keys()))
        deactivated_count = 0
        if missing_ids:
            deactivated_count = Student.objects.filter(
                api_id__in=missing_ids).update(active=False)

    return {
        "total_students": len(all_students),
        "created": len(to_create),
        "updated": len(to_update),
        "deactivated": deactivated_count
    }


async def sync_students():
    url_endpoint = "student-list"
    all_students = await fetch_all_pages(
        url_endpoint=url_endpoint,
        item_key="items"
    )

    if not all_students:
        return {"total_students": 0, "created": 0, "updated": 0, "deactivated": 0}

    result = await _save_students_to_db(all_students)

    return result
