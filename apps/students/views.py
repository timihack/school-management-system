from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import StudentFilterParams
from .forms import StudentCreateForm, StudentUpdateForm
from .models import Student
from .services import StudentCreateData


class StudentListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_STUDENTS
    PAGE_SIZE = 10

    def get(self, request):
        filters = StudentFilterParams.from_request(request)
        student_qs = selectors.get_student_list(
            search=filters.search,
            is_active=filters.is_active_filter,
        )

        paginator = Paginator(student_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        # HTMX partial swap: only the table + pagination re-render on
        # search/filter/page changes, not the whole page shell.
        if request.htmx:
            return render(request, "students/partials/student_table.html", context)

        return render(request, "students/student_list.html", context)


class StudentCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_STUDENTS

    def get(self, request):
        return render(request, "students/student_form.html", {"form": StudentCreateForm()})

    def post(self, request):
        form = StudentCreateForm(request.POST)
        if not form.is_valid():
            return render(request, "students/student_form.html", {"form": form})

        data = StudentCreateData(**form.cleaned_data)
        student, temporary_password = services.create_student(data)

        messages.success(
            request,
            f"Student '{student}' created. Temporary password: {temporary_password} "
            "(shown once only - share it securely with the student).",
        )
        return redirect("students:detail", pk=student.pk)


class StudentDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_STUDENTS

    def get(self, request, pk):
        student = get_object_or_404(selectors.get_student_list(), pk=pk)
        guardianships = student.guardianships.select_related("parent__user")
        return render(
            request,
            "students/student_detail.html",
            {"student": student, "guardianships": guardianships},
        )


class StudentUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_STUDENTS

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentUpdateForm(instance=student)
        return render(request, "students/student_form.html", {"form": form, "student": student})

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentUpdateForm(request.POST, instance=student)
        if not form.is_valid():
            return render(
                request, "students/student_form.html", {"form": form, "student": student}
            )

        form.save()
        messages.success(request, "Student updated.")
        return redirect("students:detail", pk=student.pk)


class StudentDeactivateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_DEACTIVATE_STUDENTS

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        services.deactivate_student(student)

        # HTMX request: swap just the status badge in place.
        if request.htmx:
            return render(
                request, "students/partials/student_status_badge.html", {"student": student}
            )

        messages.success(request, f"{student} has been deactivated.")
        return redirect("students:detail", pk=student.pk)