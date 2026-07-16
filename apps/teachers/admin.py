from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user", "qualification", "is_active", "date_joined")
    list_filter = ("is_active",)
    search_fields = ("employee_id", "user__first_name", "user__last_name", "qualification")