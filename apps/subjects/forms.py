from django import forms

from .models import AssessmentComponent, GradeBand, SkillChecklistItem, Subject
from .validators import validate_grade_band_does_not_overlap

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class SubjectForm(forms.ModelForm):
    """
    ONE form for both create and update, like Department (Phase 7) and
    ClassLevel (Phase 8) - creating a Subject never spans two models.
    """

    class Meta:
        model = Subject
        fields = ["name", "code", "assessment_type", "computation_method", "class_levels", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "assessment_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "computation_method": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "class_levels": forms.SelectMultiple(attrs={"class": TAILWIND_INPUT, "size": 6}),
        }


class AssessmentComponentForm(forms.ModelForm):
    """
    Initial values pre-fill a common default split (CA1=10, CA2=10,
    CA3=20, Exam=60) purely to make manual entry faster for the common
    case - this is a FORM convenience, not a database-backed template
    (see this phase's write-up for why a formal "default template"
    model was deliberately left out).
    """

    class Meta:
        model = AssessmentComponent
        fields = ["name", "component_type", "max_score", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "component_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "max_score": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
        }


class SkillChecklistItemForm(forms.ModelForm):
    class Meta:
        model = SkillChecklistItem
        fields = ["description", "order"]
        widgets = {
            "description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
        }


class GradeBandForm(forms.ModelForm):
    """
    Takes `grading_scale` via __init__ (not a form field) so clean() can
    check the new/edited range against every OTHER band under the same
    scale - same pattern as GuardianshipCreateForm taking `parent` via
    __init__ in Phase 4.
    """

    class Meta:
        model = GradeBand
        fields = ["label", "description", "min_percentage", "max_percentage"]
        widgets = {
            "label": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "min_percentage": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "max_percentage": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, grading_scale=None, **kwargs):
        self.grading_scale = grading_scale
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        min_percentage = cleaned_data.get("min_percentage")
        max_percentage = cleaned_data.get("max_percentage")

        if min_percentage is not None and max_percentage is not None:
            validate_grade_band_does_not_overlap(
                grading_scale=self.grading_scale or self.instance.grading_scale,
                min_percentage=min_percentage,
                max_percentage=max_percentage,
                exclude_pk=self.instance.pk,
            )

        return cleaned_data