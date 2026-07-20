from django import forms

from apps.teachers.models import Teacher

from .models import ClassArm, ClassLevel, PromotionPolicy
from .validators import validate_promotion_policy_consistency

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)
TAILWIND_CHECKBOX = "rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"


class ClassLevelForm(forms.ModelForm):
    """
    ONE form for both create and update - like Department (Phase 7),
    creating a ClassLevel never spans two models, so no Form/ModelForm
    split is needed here.
    """

    class Meta:
        model = ClassLevel
        fields = [
            "name",
            "category",
            "order",
            "has_arms",
            "assessment_type",
            "promotes_to",
            "exit_requires_arm_placement",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "category": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "has_arms": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "assessment_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "promotes_to": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "exit_requires_arm_placement": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["promotes_to"].required = False
        # A level can't promote to itself - only relevant once it
        # already exists (on create there's no self to exclude yet).
        if self.instance.pk:
            self.fields["promotes_to"].queryset = ClassLevel.objects.exclude(pk=self.instance.pk)


class ClassArmForm(forms.ModelForm):
    class Meta:
        model = ClassArm
        fields = ["name", "class_teacher"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "class_teacher": forms.Select(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_teacher"].required = False
        self.fields["class_teacher"].queryset = Teacher.objects.filter(is_active=True)


class PromotionPolicyForm(forms.ModelForm):
    class Meta:
        model = PromotionPolicy
        fields = [
            "pass_percentage",
            "promotion_basis",
            "cumulative_method",
            "gatekeeper_pass_mark_mode",
            "gatekeeper_custom_pass_mark",
            "gatekeeper_logic",
            "gatekeeper_subjects",
            "skill_based_promotion_mode",
        ]
        widgets = {
            "pass_percentage": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "promotion_basis": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "cumulative_method": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "gatekeeper_pass_mark_mode": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "gatekeeper_custom_pass_mark": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "gatekeeper_logic": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "gatekeeper_subjects": forms.SelectMultiple(attrs={"class": TAILWIND_INPUT, "size": 6}),
            "skill_based_promotion_mode": forms.Select(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restricted to subjects actually taught at THIS level, reached
        # purely via the reverse relation (class_level.subjects) - no
        # `from apps.subjects.models import Subject` needed here, so
        # apps.classes stays Python-import-decoupled from apps.subjects
        # even though the underlying data relationship now points both
        # ways.
        self.fields["gatekeeper_subjects"].queryset = self.instance.class_level.subjects.all()

    def clean(self):
        cleaned_data = super().clean()
        validate_promotion_policy_consistency(
            class_level=self.instance.class_level,
            gatekeeper_pass_mark_mode=cleaned_data.get("gatekeeper_pass_mark_mode"),
            gatekeeper_custom_pass_mark=cleaned_data.get("gatekeeper_custom_pass_mark"),
            skill_based_promotion_mode=cleaned_data.get("skill_based_promotion_mode", ""),
        )
        return cleaned_data


class ClassEnrollmentForm(forms.Form):
    """
    Plain Form - the student is implied by the URL, not a form field.

    class_arm's valid choices really depend on WHICH class_level is
    picked (only arms belonging to that level should be selectable) -
    that's exactly the kind of dynamic-dropdown UX that needs JS/HTMX,
    which is deferred to the design-system phase per project convention
    (no UI polish per module). For now this shows ALL arms and relies on
    clean() to catch a mismatched pairing rather than preventing it at
    the widget level - a real usability rough edge, tracked for revisit
    later, not silently ignored.
    """

    class_level = forms.ModelChoiceField(
        queryset=ClassLevel.objects.all(), widget=forms.Select(attrs={"class": TAILWIND_INPUT})
    )
    class_arm = forms.ModelChoiceField(
        queryset=ClassArm.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": TAILWIND_INPUT}),
    )
    is_repeat = forms.BooleanField(
        required=False,
        label="This is a repeat of the same level",
        widget=forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
    )

    def clean(self):
        cleaned_data = super().clean()
        class_level = cleaned_data.get("class_level")
        class_arm = cleaned_data.get("class_arm")

        if class_level and class_level.has_arms and not class_arm:
            raise forms.ValidationError(f"{class_level.name} requires an arm to be selected.")

        if class_level and class_arm and class_arm.class_level_id != class_level.pk:
            raise forms.ValidationError(
                "The selected arm does not belong to the selected class level."
            )

        if class_level and not class_level.has_arms and class_arm:
            raise forms.ValidationError(f"{class_level.name} does not use arms - leave this blank.")

        return cleaned_data