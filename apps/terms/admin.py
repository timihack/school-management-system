from django.contrib import admin

from .models import AcademicSession, Term


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("academic_session", "name", "sequence", "is_current", "start_date", "end_date")
    list_filter = ("academic_session", "name", "is_current")