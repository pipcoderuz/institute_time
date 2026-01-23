from django.contrib import admin
from .models.groups import Group
from .models.specialty import Specialty
from .models.department import Department
from .models.curriculum import Curriculum
from .models.auditorium import Auditorium
from .models.subjects import Subjects
from .models.curriculum_subjects import CurriculumSubject
from .models.student import Student
# Register your models here.

admin.site.register(Group)
admin.site.register(Department)
admin.site.register(Specialty)
admin.site.register(Curriculum)
admin.site.register(Auditorium)
admin.site.register(Subjects)
admin.site.register(CurriculumSubject)


class StudentAdmin(admin.ModelAdmin):
    search_fields = ('full_name', 'hemis_student_id_number', 'student_passport_id')

admin.site.register(Student, StudentAdmin)