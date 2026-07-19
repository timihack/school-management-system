from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.students.models import Student
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import ClassLevelFilterParams
from .forms import ClassArmForm, ClassEnrollmentForm, ClassLevelForm, PromotionPolicyForm
from .models import ClassArm, ClassLevel


class ClassLevelListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_CLASSES
    PAGE_SIZE = 15

    def get(self, request):
        filters = ClassLevelFilterParams.from_request(request)
        class_level_qs = selectors.get_class_level_list(search=filters.search)

        paginator = Paginator(class_level_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "classes/partials/class_level_table.html", context)

        return render(request, "classes/class_level_list.html", context)


class ClassLevelCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def get(self, request):
        return render(request, "classes/class_level_form.html", {"form": ClassLevelForm()})

    def post(self, request):
        form = ClassLevelForm(request.POST)
        if not form.is_valid():
            return render(request, "classes/class_level_form.html", {"form": form})

        class_level = form.save()
        # Every level gets a default policy the moment it's created -
        # see services.ensure_promotion_policy_exists for why.
        services.ensure_promotion_policy_exists(class_level)

        messages.success(request, f"Class level '{class_level}' created.")
        return redirect("classes:detail", pk=class_level.pk)


class ClassLevelDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_CLASSES

    def get(self, request, pk):
        class_level = get_object_or_404(ClassLevel, pk=pk)
        arms = selectors.get_arms_for_level(class_level)
        policy = services.ensure_promotion_policy_exists(class_level)
        return render(
            request,
            "classes/class_level_detail.html",
            {"class_level": class_level, "arms": arms, "policy": policy},
        )


class ClassLevelUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def get(self, request, pk):
        class_level = get_object_or_404(ClassLevel, pk=pk)
        form = ClassLevelForm(instance=class_level)
        return render(
            request, "classes/class_level_form.html", {"form": form, "class_level": class_level}
        )

    def post(self, request, pk):
        class_level = get_object_or_404(ClassLevel, pk=pk)
        form = ClassLevelForm(request.POST, instance=class_level)
        if not form.is_valid():
            return render(
                request,
                "classes/class_level_form.html",
                {"form": form, "class_level": class_level},
            )

        form.save()
        messages.success(request, "Class level updated.")
        return redirect("classes:detail", pk=class_level.pk)


class ClassLevelDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def post(self, request, pk):
        class_level = get_object_or_404(ClassLevel, pk=pk)
        name = str(class_level)
        # PROTECT on ClassEnrollment.class_level means this raises
        # ProtectedError (surfacing as a 500 for now) if any enrollment
        # history references it. A friendlier catch-and-message belongs
        # to a later UI-polish pass, not this phase.
        class_level.delete()
        messages.success(request, f"'{name}' deleted.")
        return redirect("classes:list")


class ClassArmCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def get(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        form = ClassArmForm()
        return render(
            request, "classes/class_arm_form.html", {"form": form, "class_level": class_level}
        )

    def post(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        form = ClassArmForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "classes/class_arm_form.html",
                {"form": form, "class_level": class_level},
            )

        arm = form.save(commit=False)
        arm.class_level = class_level
        arm.save()

        messages.success(request, f"Arm '{arm}' created.")
        return redirect("classes:detail", pk=class_level.pk)


class ClassArmUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def get(self, request, pk):
        arm = get_object_or_404(ClassArm, pk=pk)
        form = ClassArmForm(instance=arm)
        return render(
            request,
            "classes/class_arm_form.html",
            {"form": form, "class_level": arm.class_level, "arm": arm},
        )

    def post(self, request, pk):
        arm = get_object_or_404(ClassArm, pk=pk)
        form = ClassArmForm(request.POST, instance=arm)
        if not form.is_valid():
            return render(
                request,
                "classes/class_arm_form.html",
                {"form": form, "class_level": arm.class_level, "arm": arm},
            )

        form.save()
        messages.success(request, "Arm updated.")
        return redirect("classes:detail", pk=arm.class_level.pk)


class ClassArmDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_CLASSES

    def post(self, request, pk):
        arm = get_object_or_404(ClassArm, pk=pk)
        class_level_pk = arm.class_level_id
        name = str(arm)
        arm.delete()
        messages.success(request, f"Arm '{name}' deleted.")
        return redirect("classes:detail", pk=class_level_pk)


class PromotionPolicyUpdateView(RoleRequiredMixin, View):
    """
    Always an update, never a create - ensure_promotion_policy_exists()
    guarantees the row already exists by the time anyone reaches this
    view, since it's called the moment the ClassLevel itself was
    created.
    """

    allowed_roles = permissions.CAN_MANAGE_PROMOTION_POLICY

    def get(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        policy = services.ensure_promotion_policy_exists(class_level)
        form = PromotionPolicyForm(instance=policy)
        return render(
            request,
            "classes/promotion_policy_form.html",
            {"form": form, "class_level": class_level},
        )

    def post(self, request, level_pk):
        class_level = get_object_or_404(ClassLevel, pk=level_pk)
        policy = services.ensure_promotion_policy_exists(class_level)
        form = PromotionPolicyForm(request.POST, instance=policy)
        if not form.is_valid():
            return render(
                request,
                "classes/promotion_policy_form.html",
                {"form": form, "class_level": class_level},
            )

        form.save()
        messages.success(request, "Promotion policy updated.")
        return redirect("classes:detail", pk=class_level.pk)


class ClassEnrollmentCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_ENROLLMENT

    def get(self, request, student_pk):
        student = get_object_or_404(Student, pk=student_pk)
        form = ClassEnrollmentForm()
        return render(request, "classes/enrollment_form.html", {"form": form, "student": student})

    def post(self, request, student_pk):
        student = get_object_or_404(Student, pk=student_pk)
        form = ClassEnrollmentForm(request.POST)
        if not form.is_valid():
            return render(
                request, "classes/enrollment_form.html", {"form": form, "student": student}
            )

        services.assign_student_to_class(
            student=student,
            class_level=form.cleaned_data["class_level"],
            class_arm=form.cleaned_data.get("class_arm"),
            assigned_by=request.user,
            is_repeat=form.cleaned_data["is_repeat"],
        )
        messages.success(request, f"{student} assigned to class.")
        return redirect("students:detail", pk=student.pk)