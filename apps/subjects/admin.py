from django.contrib import admin

from .models import (
    AssessmentComponent,
    GradeBand,
    GradingScale,
    SkillChecklistItem,
    Subject,
    Topic,
)


class AssessmentComponentInline(admin.TabularInline):
    model = AssessmentComponent
    extra = 1


class SkillChecklistItemInline(admin.TabularInline):
    model = SkillChecklistItem
    extra = 1


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "assessment_type", "is_active")
    list_filter = ("assessment_type", "is_active")
    search_fields = ("name", "code")
    inlines = [AssessmentComponentInline, SkillChecklistItemInline]


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ("class_level", "name")


class GradeBandInline(admin.TabularInline):
    model = GradeBand
    extra = 1


@admin.register(GradeBand)
class GradeBandAdmin(admin.ModelAdmin):
    list_display = ("grading_scale", "label", "min_percentage", "max_percentage")
    list_filter = ("grading_scale",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "class_level", "term", "order")
    list_filter = ("class_level", "subject", "term")
    search_fields = ("name", "subject__name")