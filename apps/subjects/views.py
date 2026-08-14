from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.classes.models import ClassLevel
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import SubjectFilterParams
from .forms import (
    AssessmentComponentForm,
    GradeBandForm,
    SkillChecklistItemForm,
    SubjectForm,
    TopicForm,
)
from .models import AssessmentComponent, GradeBand, SkillChecklistItem, Subject, Topic


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
        topics = selectors.get_topics_for_subject(subject)
        return render(
            request,
            "subjects/subject_detail.html",
            {
                "subject": subject,
                "components": components,
                "skill_items": skill_items,
                "topics": topics,
            },
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


class TopicCreateView(RoleRequiredMixin, View):
    """
    Nested under subject_pk, same shape as AssessmentComponentCreateView
    - subject is resolved from the URL and set on the instance before
    save(), never a form field. Also passes `subject` into TopicForm so
    its class_level dropdown is scoped to levels this subject is
    actually assigned to.
    """

    allowed_roles = permissions.CAN_MANAGE_TOPICS

    def get(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = TopicForm(subject=subject)
        return render(request, "subjects/topic_form.html", {"form": form, "subject": subject})

    def post(self, request, subject_pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        form = TopicForm(request.POST, subject=subject)
        if not form.is_valid():
            return render(
                request, "subjects/topic_form.html", {"form": form, "subject": subject}
            )

        topic = form.save(commit=False)
        topic.subject = subject
        topic.save()

        messages.success(request, f"Topic '{topic}' added.")
        return redirect("subjects:detail", pk=subject.pk)


class TopicUpdateView(RoleRequiredMixin, View):
    """
    Also nested under subject_pk (unlike the flat Delete views below) -
    needed so TopicForm can re-scope class_level to the right subject's
    levels on edit, not just on create. The `subject=subject` filter on
    get_object_or_404 is a defense-in-depth check: a URL requesting
    topic pk under the wrong subject_pk 404s instead of silently editing
    a topic that doesn't belong to that subject.
    """

    allowed_roles = permissions.CAN_MANAGE_TOPICS

    def get(self, request, subject_pk, pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        topic = get_object_or_404(Topic, pk=pk, subject=subject)
        form = TopicForm(instance=topic, subject=subject)
        return render(
            request,
            "subjects/topic_form.html",
            {"form": form, "subject": subject, "topic": topic},
        )

    def post(self, request, subject_pk, pk):
        subject = get_object_or_404(Subject, pk=subject_pk)
        topic = get_object_or_404(Topic, pk=pk, subject=subject)
        form = TopicForm(request.POST, instance=topic, subject=subject)
        if not form.is_valid():
            return render(
                request,
                "subjects/topic_form.html",
                {"form": form, "subject": subject, "topic": topic},
            )

        form.save()
        messages.success(request, "Topic updated.")
        return redirect("subjects:detail", pk=subject.pk)


class TopicDeleteView(RoleRequiredMixin, View):
    """
    Flat (pk only), same convention as AssessmentComponentDeleteView/
    SkillChecklistItemDeleteView - subject_pk is derived from the
    instance itself before delete, not taken from the URL.
    """

    allowed_roles = permissions.CAN_MANAGE_TOPICS

    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        subject_pk = topic.subject_id
        topic.delete()
        messages.success(request, "Topic removed.")
        return redirect("subjects:detail", pk=subject_pk)


class CurriculumOverviewView(RoleRequiredMixin, View):
    """
    Reached from the ClassLevel detail page (apps.classes), alongside
    the existing Grading Scale / Promotion Policy links. Shows every
    Topic across every Subject for one ClassLevel, grouped by subject.

    Resolves this phase's open design question by reusing the existing
    policy constants rather than inventing a dedicated one: viewing the
    overview is a "can see subjects/curriculum" concern, so it shares
    CAN_VIEW_SUBJECTS with SubjectDetailView and GradingScaleDetailView.
    The actual create/update/delete actions reachable from this page
    are separately gated by CAN_MANAGE_TOPICS on their own views, same
    as GradingScaleDetailView (view-only) delegates management to
    GradeBandCreateView/DeleteView (CAN_MANAGE_GRADING_SCALE).
    """

    allowed_roles = permissions.CAN_VIEW_SUBJECTS

    def get(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        grouped_topics = selectors.get_topics_for_level(class_level)
        return render(
            request,
            "subjects/curriculum_overview.html",
            {"class_level": class_level, "grouped_topics": grouped_topics},
        )