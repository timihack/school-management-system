from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "user", "gender", "is_active", "admission_date")
    list_filter = ("gender", "is_active")
    search_fields = ("admission_number", "user__first_name", "user__last_name", "user__username")