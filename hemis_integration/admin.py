from django.contrib import admin
from .models.groups import Group
from .models.specialty import Specialty
from .models.department import Department
from .models.curriculum import Curriculum
from .models.auditorium import Auditorium
# Register your models here.

admin.site.register(Group)
admin.site.register(Department)
admin.site.register(Specialty)
admin.site.register(Curriculum)
admin.site.register(Auditorium)
