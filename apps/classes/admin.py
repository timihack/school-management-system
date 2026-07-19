from django.contrib import admin

from .models import ClassArm, ClassEnrollment, ClassLevel, PromotionPolicy


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order", "has_arms", "assessment_type")
    list_filter = ("category", "has_arms", "assessment_type")
    search_fields = ("name",)


@admin.register(ClassArm)
class ClassArmAdmin(admin.ModelAdmin):
    list_display = ("name", "class_level", "class_teacher")
    list_filter = ("class_level",)


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "class_level", "class_arm", "is_current", "is_repeat", "assigned_on")
    list_filter = ("class_level", "is_current", "is_repeat")
    search_fields = ("student__admission_number", "student__user__last_name")


@admin.register(PromotionPolicy)
class PromotionPolicyAdmin(admin.ModelAdmin):
    list_display = ("class_level", "pass_percentage", "promotion_basis")