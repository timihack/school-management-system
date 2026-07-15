from django.contrib import admin

from .models import Guardianship, Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("user", "occupation", "phone_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("user__first_name", "user__last_name", "user__email")


@admin.register(Guardianship)
class GuardianshipAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "relationship", "is_primary_contact", "can_pickup")
    list_filter = ("relationship", "is_primary_contact", "can_pickup")
    search_fields = ("parent__user__last_name", "student__user__last_name", "student__admission_number")