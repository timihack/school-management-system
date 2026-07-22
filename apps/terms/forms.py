from django import forms

from .models import AcademicSession, Term
from .validators import validate_start_before_end, validate_term_within_session

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "start_date", "end_date"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "2024/2025"}),
            "start_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        validate_start_before_end(cleaned_data.get("start_date"), cleaned_data.get("end_date"))
        return cleaned_data


class TermForm(forms.ModelForm):
    """
    Takes `session` via __init__ (not a form field, since it's implied
    by the URL) so clean() can check the term's dates fall within that
    session's dates - same __init__-scoping pattern as GuardianshipCreateForm
    (Phase 4) and GradeBandForm (Phase 9).
    """

    class Meta:
        model = Term
        fields = [
            "name",
            "sequence",
            "start_date",
            "end_date",
            "next_term_begins",
            "total_school_days",
        ]
        widgets = {
            "name": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "sequence": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "start_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "next_term_begins": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "total_school_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, session: AcademicSession | None = None, **kwargs):
        self.session = session
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        session = self.session or (self.instance.academic_session if self.instance.pk else None)

        validate_start_before_end(cleaned_data.get("start_date"), cleaned_data.get("end_date"))

        if session:
            validate_term_within_session(
                term_start=cleaned_data.get("start_date"),
                term_end=cleaned_data.get("end_date"),
                session=session,
            )

        return cleaned_data