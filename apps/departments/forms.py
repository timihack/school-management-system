from django import forms

from apps.accounts.models import User

from .models import Department

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class DepartmentForm(forms.ModelForm):
    """
    ONE form for both create and update - unlike every person-
    representing app so far, creating a Department never spans two
    models (there's no User/login to create alongside it), so there's
    no need for the plain-Form-for-create / ModelForm-for-update split
    that Student/Parent/Teacher/Staff all needed.
    """

    class Meta:
        model = Department
        fields = ["name", "description", "head_of_department"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3}),
            "head_of_department": forms.Select(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Explicit queryset restriction, even though the model's
        # limit_choices_to already achieves the same result for
        # ModelForm-generated fields - being explicit here makes the
        # rule visible and testable directly in this file, rather than
        # relying on a reader already knowing limit_choices_to's effect
        # on auto-generated form fields.
        self.fields["head_of_department"].queryset = User.objects.filter(
            role__in=[User.Role.TEACHER, User.Role.STAFF]
        )
        self.fields["head_of_department"].required = False