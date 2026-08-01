import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.classes.models import ClassArm, ClassLevel
from apps.terms.selectors import get_current_term
from core.permissions.checks import check_role_or_owner
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .forms import parse_attendance_submission


def _can_mark_for(user, *, class_level, class_arm) -> bool:
    """
    True if `user` is the designated teacher for the roster being
    marked. Branches the SAME way selectors.get_roster does: if an arm
    is involved, check the ARM's class_teacher; otherwise (a no-arm
    level) check the LEVEL's own class_teacher. hasattr() safely probes
    the optional OneToOne reverse relation without raising
    RelatedObjectDoesNotExist for non-teacher users.
    """
    if not hasattr(user, "teacher_profile"):
        return False
    teacher_id = user.teacher_profile.id
    if class_arm is not None:
        return class_arm.class_teacher_id == teacher_id
    return class_level.class_teacher_id == teacher_id


class AttendanceRegisterView(RoleRequiredMixin, View):
    """
    Broad gate first (RoleRequiredMixin: Admin/Staff/Teacher can all
    REACH this page - Student/Parent cannot). Then, once a specific
    class_level (and, if it has arms, a class_arm) is resolved,
    check_role_or_owner narrows further: Admin/Staff can mark ANY class;
    a Teacher only the one(s) they're personally responsible for -
    which is the ARM's class_teacher when arms exist, or the LEVEL's own
    class_teacher when they don't (see _can_mark_for above).
    """

    allowed_roles = permissions.CAN_VIEW_ATTENDANCE

    def _resolve_class_level(self, request):
        pk = request.GET.get("class_level") or request.POST.get("class_level")
        if pk:
            return get_object_or_404(ClassLevel, pk=pk)

        # No level specified - default a Teacher to a level they
        # directly form-teach (the no-arm case only; arm-based defaults
        # are resolved separately in _resolve_class_arm below).
        if hasattr(request.user, "teacher_profile"):
            return ClassLevel.objects.filter(
                class_teacher=request.user.teacher_profile
            ).first()
        return None

    def _resolve_class_arm(self, request, class_level):
        """
        Returns None outright if class_level has no arms - callers must
        never treat a None here as "not yet chosen" when has_arms is
        False; it means "this class genuinely has no arm concept."
        """
        if class_level is None or not class_level.has_arms:
            return None

        pk = request.GET.get("class_arm") or request.POST.get("class_arm")
        if pk:
            return get_object_or_404(ClassArm, pk=pk)

        if hasattr(request.user, "teacher_profile"):
            return ClassArm.objects.filter(
                class_level=class_level, class_teacher=request.user.teacher_profile
            ).first()
        return None

    def _resolve_date(self, request) -> datetime.date:
        date_str = request.GET.get("date") or request.POST.get("date")
        if date_str:
            return datetime.date.fromisoformat(date_str)
        return datetime.date.today()

    def get(self, request):
        class_level = self._resolve_class_level(request)
        class_arm = self._resolve_class_arm(request, class_level)
        selected_date = self._resolve_date(request)
        all_levels = ClassLevel.objects.all()
        arms_for_level = (
            ClassArm.objects.filter(class_level=class_level).select_related("class_teacher__user")
            if class_level and class_level.has_arms
            else ClassArm.objects.none()
        )

        context = {
            "all_levels": all_levels,
            "arms_for_level": arms_for_level,
            "selected_class_level": class_level,
            "selected_class_arm": class_arm,
            "selected_date": selected_date,
        }

        # A level with has_arms=True genuinely needs an arm chosen
        # before a roster can be resolved at all - this is NOT the same
        # as "no level chosen yet," so it gets its own message rather
        # than silently falling through.
        needs_arm_selection = (
            class_level is not None and class_level.has_arms and class_arm is None
        )
        context["needs_arm_selection"] = needs_arm_selection

        if class_level is not None and not needs_arm_selection:
            check_role_or_owner(
                request=request,
                allowed_roles=permissions.CAN_MARK_ATTENDANCE_BROADLY,
                is_owner=_can_mark_for(request.user, class_level=class_level, class_arm=class_arm),
            )

            roster = selectors.get_roster(class_level=class_level, class_arm=class_arm)
            existing_records = {
                record.student_id: record
                for record in selectors.get_attendance_for_date(
                    class_level=class_level, class_arm=class_arm, date=selected_date
                )
            }
            context["roster"] = [
                {"student": student, "existing_record": existing_records.get(student.pk)}
                for student in roster
            ]

        # HTMX partial swap: changing level/arm/date re-renders only the
        # picker+roster block, matching every other list page's
        # search/filter pattern in this project - not a full page reload.
        if request.htmx:
            return render(request, "attendance/partials/picker_and_roster.html", context)

        return render(request, "attendance/register.html", context)

    def post(self, request):
        class_level = self._resolve_class_level(request)
        class_arm = self._resolve_class_arm(request, class_level)
        selected_date = self._resolve_date(request)

        if class_level is None:
            messages.error(request, "Select a class before submitting attendance.")
            return redirect("attendance:register")

        if class_level.has_arms and class_arm is None:
            messages.error(request, "Select an arm before submitting attendance.")
            return redirect("attendance:register")

        check_role_or_owner(
            request=request,
            allowed_roles=permissions.CAN_MARK_ATTENDANCE_BROADLY,
            is_owner=_can_mark_for(request.user, class_level=class_level, class_arm=class_arm),
        )

        term = get_current_term()
        if term is None:
            messages.error(request, "No current term is active - ask an admin to activate one.")
            return redirect("attendance:register")

        roster = selectors.get_roster(class_level=class_level, class_arm=class_arm)
        student_ids = [student.pk for student in roster]
        attendance_data = parse_attendance_submission(request.POST, student_ids)

        try:
            services.mark_attendance(
                class_level=class_level,
                class_arm=class_arm,
                date=selected_date,
                term=term,
                marked_by=request.user,
                attendance_data=attendance_data,
            )
        except ValidationError as exc:
            # validate_date_within_term (called inside mark_attendance)
            # raises this when the submitted date falls outside the
            # current term's start/end range - e.g. marking attendance
            # for "today" when the active term hasn't started yet, or
            # has already ended. Every other error path in this view
            # already redirects with a message rather than letting an
            # exception propagate into a 500 - this one was missed when
            # the service was first wired up.
            messages.error(request, " ".join(exc.messages))
            return redirect("attendance:register")

        class_name = f"{class_level.name} {class_arm.name}" if class_arm else class_level.name
        messages.success(request, f"Attendance saved for {class_name} on {selected_date}.")

        redirect_url = f"/attendance/?class_level={class_level.pk}&date={selected_date}"
        if class_arm:
            redirect_url += f"&class_arm={class_arm.pk}"
        return redirect(redirect_url)