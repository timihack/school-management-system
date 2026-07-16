from datetime import date

from django.core.exceptions import ValidationError


def validate_teacher_date_of_birth(date_of_birth: date) -> None:
    """
    A teacher must plausibly be an adult (>=18) and not implausibly old
    (>100) at the point of hire. This deliberately does NOT reuse
    apps.students.validators.validate_date_of_birth_is_plausible, even
    though both validate "a date of birth" - they encode two genuinely
    different business rules (student age range vs. adult employee age
    range) that only coincidentally look similar. Sharing the function
    would create a cross-app dependency for a coincidence, not a real
    shared concept.
    """
    today = date.today()

    if date_of_birth > today:
        raise ValidationError("Date of birth cannot be in the future.")

    age_years = (today - date_of_birth).days / 365.25
    if age_years < 18:
        raise ValidationError("A teacher must be at least 18 years old.")
    if age_years > 100:
        raise ValidationError(
            "Date of birth makes this teacher older than 100 - please double check."
        )


def validate_date_joined_not_in_future(date_joined: date) -> None:
    if date_joined > date.today():
        raise ValidationError("Date joined cannot be in the future.")