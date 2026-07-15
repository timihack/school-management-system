from django import forms

from apps.accounts.models import User
from apps.students.models import Student

from .models import Guardianship, Parent

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class ParentCreateForm(forms.Form):
    """
    Plain Form, same reasoning as StudentCreateForm - this spans two
    models (User + Parent) via create_parent().
    """

    first_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    last_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": TAILWIND_INPUT}))
    occupation = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    phone_number = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    address = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3})
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class ParentUpdateForm(forms.ModelForm):
    """ModelForm - editing only ever touches the Parent model itself."""

    class Meta:
        model = Parent
        fields = ["occupation", "phone_number", "address"]
        widgets = {
            "occupation": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "phone_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3}),
        }


class GuardianshipCreateForm(forms.Form):
    """
    Links an existing student to a parent, looked up by admission number
    rather than a giant dropdown of every student in the school - staff
    creating this link already know the child's admission number, and a
    searchable-select widget is exactly the kind of UI polish deferred
    to the design-system phase.

    Takes `parent` in __init__ (not a form field) so clean() can check
    for an existing link to THIS specific parent - the form needs to
    know which parent it's being submitted for to catch duplicates
    before they ever reach the database constraint.
    """

    student_admission_number = forms.CharField(
        max_length=20,
        label="Student admission number",
        widget=forms.TextInput(attrs={"class": TAILWIND_INPUT}),
    )
    relationship = forms.ChoiceField(
        choices=Guardianship.Relationship.choices,
        widget=forms.Select(attrs={"class": TAILWIND_INPUT}),
    )
    is_primary_contact = forms.BooleanField(required=False, label="Primary contact")
    can_pickup = forms.BooleanField(required=False, initial=True, label="Authorized to pick up")

    def __init__(self, *args, parent: Parent | None = None, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)

    def clean_student_admission_number(self):
        admission_number = self.cleaned_data["student_admission_number"]
        try:
            student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            raise forms.ValidationError(
                f"No student found with admission number '{admission_number}'."
            )
        self.cleaned_data["student"] = student
        return admission_number

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")

        if student and self.parent and Guardianship.objects.filter(
            parent=self.parent, student=student
        ).exists():
            raise forms.ValidationError(f"{student} is already linked to this parent.")

        return cleaned_data