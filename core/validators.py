from datetime import date

from django.core.exceptions import ValidationError


def validate_adult_employee_date_of_birth(date_of_birth: date) -> None:
    """
    Shared bounds for "an adult employed by the school" - used by both
    Teacher and Staff. This is DIFFERENT from the earlier decision not to
    share validate_date_of_birth_is_plausible between Student and
    Teacher: that was two DIFFERENT rules that happened to look similar
    (student age range vs. adult age range). This one is the SAME rule
    used by two apps - that's what makes extracting it to core/ correct
    here, and would have been wrong there.
    """
    today = date.today()

    if date_of_birth > today:
        raise ValidationError("Date of birth cannot be in the future.")

    age_years = (today - date_of_birth).days / 365.25
    if age_years < 18:
        raise ValidationError("Must be at least 18 years old.")
    if age_years > 100:
        raise ValidationError(
            "Date of birth makes this person older than 100 - please double check."
        )


def validate_date_not_in_future(the_date: date) -> None:
    if the_date > date.today():
        raise ValidationError("Date cannot be in the future.")