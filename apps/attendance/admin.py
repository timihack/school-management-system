from django.contrib import admin

from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "class_arm", "term", "date", "status", "marked_by")
    list_filter = ("class_arm", "term", "status", "date")
    search_fields = ("student__admission_number", "student__user__last_name")