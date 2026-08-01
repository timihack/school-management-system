from django import forms

from apps.accounts.models import User

from .models import Student
from .validators import validate_date_of_birth_is_plausible

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class StudentCreateForm(forms.Form):
    """
    A plain Form, deliberately NOT a ModelForm - creating a student spans
    TWO models (User + Student) via the create_student() service. A
    ModelForm tied to just Student would misrepresent what actually gets
    written to the database (a whole new login-capable User included).
    """

    first_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    last_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": TAILWIND_INPUT}))
    admission_number = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"})
    )
    gender = forms.ChoiceField(
        choices=Student.Gender.choices, widget=forms.Select(attrs={"class": TAILWIND_INPUT})
    )
    admission_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"})
    )
    address = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3})
    )
    phone_number = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )

    def clean_admission_number(self):
        admission_number = self.cleaned_data["admission_number"]
        if Student.objects.filter(admission_number=admission_number).exists():
            raise forms.ValidationError(
                f"Admission number '{admission_number}' is already in use."
            )
        return admission_number

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]
        validate_date_of_birth_is_plausible(date_of_birth)
        return date_of_birth

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class StudentUpdateForm(forms.ModelForm):
    """
    A genuine ModelForm - unlike creation, editing contact details only
    touches the Student model, so there's no dual-model complexity to
    hide. admission_number and date_of_birth are intentionally NOT
    editable here: they're historical/identity facts, not routine
    contact-info updates - a real correction to either should go through
    a deliberate, audited workflow later, not a casual edit form.
    """

    class Meta:
        model = Student
        fields = ["gender", "phone_number", "address", "photo"]
        widgets = {
            "gender": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "phone_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3}),
            "photo": forms.ClearableFileInput(attrs={"class": TAILWIND_INPUT}),
        }