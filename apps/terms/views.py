from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import SessionFilterParams
from .forms import AcademicSessionForm, TermForm
from .models import AcademicSession, Term


class AcademicSessionListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_TERMS
    PAGE_SIZE = 15

    def get(self, request):
        filters = SessionFilterParams.from_request(request)
        session_qs = AcademicSession.objects.all()
        if filters.search:
            session_qs = session_qs.filter(name__icontains=filters.search)

        paginator = Paginator(session_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "terms/partials/session_table.html", context)

        return render(request, "terms/session_list.html", context)


class AcademicSessionCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def get(self, request):
        return render(request, "terms/session_form.html", {"form": AcademicSessionForm()})

    def post(self, request):
        form = AcademicSessionForm(request.POST)
        if not form.is_valid():
            return render(request, "terms/session_form.html", {"form": form})

        session = form.save()
        messages.success(request, f"Session '{session}' created.")
        return redirect("terms:session_detail", pk=session.pk)


class AcademicSessionDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_TERMS

    def get(self, request, pk):
        session = get_object_or_404(AcademicSession, pk=pk)
        terms = selectors.get_terms_for_session(session)
        return render(
            request, "terms/session_detail.html", {"session": session, "terms": terms}
        )


class AcademicSessionUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def get(self, request, pk):
        session = get_object_or_404(AcademicSession, pk=pk)
        form = AcademicSessionForm(instance=session)
        return render(
            request, "terms/session_form.html", {"form": form, "session": session}
        )

    def post(self, request, pk):
        session = get_object_or_404(AcademicSession, pk=pk)
        form = AcademicSessionForm(request.POST, instance=session)
        if not form.is_valid():
            return render(
                request, "terms/session_form.html", {"form": form, "session": session}
            )

        form.save()
        messages.success(request, "Session updated.")
        return redirect("terms:session_detail", pk=session.pk)


class AcademicSessionDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def post(self, request, pk):
        session = get_object_or_404(AcademicSession, pk=pk)
        name = str(session)
        # ClassEnrollment.academic_session uses PROTECT, so this raises
        # ProtectedError (surfacing as a 500 for now) if any historical
        # enrollment references this session - same deliberate,
        # documented scope limit as ClassLevelDeleteView in Phase 8.
        session.delete()
        messages.success(request, f"'{name}' deleted.")
        return redirect("terms:session_list")


class TermCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def get(self, request, session_pk):
        session = get_object_or_404(AcademicSession, pk=session_pk)
        form = TermForm(session=session)
        return render(request, "terms/term_form.html", {"form": form, "session": session})

    def post(self, request, session_pk):
        session = get_object_or_404(AcademicSession, pk=session_pk)
        form = TermForm(request.POST, session=session)
        if not form.is_valid():
            return render(
                request, "terms/term_form.html", {"form": form, "session": session}
            )

        term = form.save(commit=False)
        term.academic_session = session
        term.save()

        messages.success(request, f"Term '{term}' created.")
        return redirect("terms:session_detail", pk=session.pk)


class TermUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def get(self, request, pk):
        term = get_object_or_404(Term, pk=pk)
        form = TermForm(instance=term, session=term.academic_session)
        return render(
            request, "terms/term_form.html", {"form": form, "session": term.academic_session, "term": term}
        )

    def post(self, request, pk):
        term = get_object_or_404(Term, pk=pk)
        form = TermForm(request.POST, instance=term, session=term.academic_session)
        if not form.is_valid():
            return render(
                request,
                "terms/term_form.html",
                {"form": form, "session": term.academic_session, "term": term},
            )

        form.save()
        messages.success(request, "Term updated.")
        return redirect("terms:session_detail", pk=term.academic_session.pk)


class TermDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def post(self, request, pk):
        term = get_object_or_404(Term, pk=pk)
        session_pk = term.academic_session_id
        name = str(term)
        term.delete()
        messages.success(request, f"'{name}' deleted.")
        return redirect("terms:session_detail", pk=session_pk)


class TermActivateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TERMS

    def post(self, request, pk):
        term = get_object_or_404(Term, pk=pk)
        services.activate_term(term)
        messages.success(request, f"{term} is now the current term.")
        return redirect("terms:session_detail", pk=term.academic_session_id)