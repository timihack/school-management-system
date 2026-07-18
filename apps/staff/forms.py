from django import forms

from apps.accounts.models import User
from apps.departments.models import Department

from .models import Staff
from .validators import validate_date_joined_not_in_future, validate_staff_date_of_birth

TAILWIND_INPUT = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class StaffCreateForm(forms.Form):
    """Plain Form - spans two models (User + Staff) via create_staff()."""

    first_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    last_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": TAILWIND_INPUT}))
    employee_id = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    job_title = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    employment_type = forms.ChoiceField(
        choices=Staff.EmploymentType.choices,
        widget=forms.Select(attrs={"class": TAILWIND_INPUT}),
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"})
    )
    date_joined = forms.DateField(
        widget=forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"})
    )
    phone_number = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": TAILWIND_INPUT})
    )
    address = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": TAILWIND_INPUT}),
    )

    def clean_employee_id(self):
        employee_id = self.cleaned_data["employee_id"]
        if Staff.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError(f"Employee ID '{employee_id}' is already in use.")
        return employee_id

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]
        validate_staff_date_of_birth(date_of_birth)
        return date_of_birth

    def clean_date_joined(self):
        date_joined = self.cleaned_data["date_joined"]
        validate_date_joined_not_in_future(date_joined)
        return date_joined


class StaffUpdateForm(forms.ModelForm):
    """ModelForm - editing only ever touches the Staff model itself."""

    class Meta:
        model = Staff
        fields = ["job_title", "employment_type", "phone_number", "address", "department"]
        widgets = {
            "job_title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "employment_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "phone_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3}),
            "department": forms.Select(attrs={"class": TAILWIND_INPUT}),
        }