from django.contrib import admin

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user", "job_title", "employment_type", "is_active")
    list_filter = ("employment_type", "is_active")
    search_fields = ("employee_id", "user__first_name", "user__last_name", "job_title")