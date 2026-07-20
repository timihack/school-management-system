from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.classes.models import ClassLevel
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import SubjectFilterParams
from .forms import AssessmentComponentForm, GradeBandForm, SkillChecklistItemForm, SubjectForm
from .models import AssessmentComponent, GradeBand, SkillChecklistItem, Subject


class SubjectListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_SUBJECTS
    PAGE_SIZE = 15

    def get(self, request):
        filters = SubjectFilterParams.from_request(request)
        subject_qs = selectors.get_subject_list(
            search=filters.search, is_active=filters.is_active_filter
        )

        paginator = Paginator(subject_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "subjects/partials/subject_table.html", context)

        return render(request, "subjects/subject_list.html", context)


class SubjectCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def get(self, request):
        return render(request, "subjects/subject_form.html", {"form": SubjectForm()})

    def post(self, request):
        form = SubjectForm(request.POST)
        if not form.is_valid():
            return render(request, "subjects/subject_form.html", {"form": form})

        subject = form.save()
        messages.success(request, f"Subject '{subject}' created.")
        return redirect("subjects:detail", pk=subject.pk)


class SubjectDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_SUBJECTS

    def get(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        components = selectors.get_components_for_subject(subject)
        skill_items = selectors.get_skill_items_for_subject(subject)
        return render(
            request,
            "subjects/subject_detail.html",
            {"subject": subject, "components": components, "skill_items": skill_items},
        )


class SubjectUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def get(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(instance=subject)
        return render(request, "subjects/subject_form.html", {"form": form, "subject": subject})

    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(request.POST, instance=subject)
        if not form.is_valid():
            return render(
                request, "subjects/subject_form.html", {"form": form, "subject": subject}
            )

        form.save()
        messages.success(request, "Subject updated.")
        return redirect("subjects:detail", pk=subject.pk)


class SubjectDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        name = str(subject)
        subject.delete()
        messages.success(request, f"'{name}' deleted.")
        return redirect("subjects:list")


class AssessmentComponentCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def get(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = AssessmentComponentForm()
        return render(
            request, "subjects/assessment_component_form.html", {"form": form, "subject": subject}
        )

    def post(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = AssessmentComponentForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "subjects/assessment_component_form.html",
                {"form": form, "subject": subject},
            )

        component = form.save(commit=False)
        component.subject = subject
        component.save()

        messages.success(request, f"Component '{component}' added.")
        return redirect("subjects:detail", pk=subject.pk)


class AssessmentComponentDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def post(self, request, pk):
        component = get_object_or_404(AssessmentComponent, pk=pk)
        subject_pk = component.subject_id
        component.delete()
        messages.success(request, "Component removed.")
        return redirect("subjects:detail", pk=subject_pk)


class SkillChecklistItemCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def get(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = SkillChecklistItemForm()
        return render(
            request, "subjects/skill_item_form.html", {"form": form, "subject": subject}
        )

    def post(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = SkillChecklistItemForm(request.POST)
        if not form.is_valid():
            return render(
                request, "subjects/skill_item_form.html", {"form": form, "subject": subject}
            )

        item = form.save(commit=False)
        item.subject = subject
        item.save()

        messages.success(request, f"Skill item '{item}' added.")
        return redirect("subjects:detail", pk=subject.pk)


class SkillChecklistItemDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_SUBJECTS

    def post(self, request, pk):
        item = get_object_or_404(SkillChecklistItem, pk=pk)
        subject_pk = item.subject_id
        item.delete()
        messages.success(request, "Skill item removed.")
        return redirect("subjects:detail", pk=subject_pk)


class GradingScaleDetailView(RoleRequiredMixin, View):
    """
    Reached from the ClassLevel detail page (apps.classes). Always shows
    a scale - services.ensure_grading_scale_exists() creates one lazily
    on first visit if it doesn't exist yet, mirroring how Phase 8's
    PromotionPolicyUpdateView always has a policy to show.
    """

    allowed_roles = permissions.CAN_VIEW_SUBJECTS

    def get(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        grading_scale = services.ensure_grading_scale_exists(class_level)
        bands = grading_scale.bands.all()
        return render(
            request,
            "subjects/grading_scale_detail.html",
            {"class_level": class_level, "grading_scale": grading_scale, "bands": bands},
        )


class GradeBandCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_GRADING_SCALE

    def get(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        grading_scale = services.ensure_grading_scale_exists(class_level)
        form = GradeBandForm(grading_scale=grading_scale)
        return render(
            request,
            "subjects/grade_band_form.html",
            {"form": form, "class_level": class_level},
        )

    def post(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        grading_scale = services.ensure_grading_scale_exists(class_level)
        form = GradeBandForm(request.POST, grading_scale=grading_scale)
        if not form.is_valid():
            return render(
                request,
                "subjects/grade_band_form.html",
                {"form": form, "class_level": class_level},
            )

        band = form.save(commit=False)
        band.grading_scale = grading_scale
        band.save()

        messages.success(request, f"Grade band '{band}' added.")
        return redirect("subjects:grading_scale_detail", level_pk=class_level.pk)


class GradeBandDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_GRADING_SCALE

    def post(self, request, pk):
        band = get_object_or_404(GradeBand, pk=pk)
        level_pk = band.grading_scale.class_level_id
        band.delete()
        messages.success(request, "Grade band removed.")
        return redirect("subjects:grading_scale_detail", level_pk=level_pk)