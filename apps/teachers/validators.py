from datetime import date

from core.validators import validate_adult_employee_date_of_birth, validate_date_not_in_future


def validate_teacher_date_of_birth(date_of_birth: date) -> None:
    """
    Delegates to the shared rule in core/validators.py - Phase 6
    confirmed this is the SAME business rule Staff needs too, not a
    coincidental lookalike (contrast with why this app deliberately does
    NOT share its rule with Student's date-of-birth check, which uses
    different bounds for a different reason). Kept as a thin wrapper
    here, rather than having forms.py import core.validators directly,
    so this app's validators.py still reads as "the business rules THIS
    app relies on," per the project's per-app validators.py convention.
    """
    validate_adult_employee_date_of_birth(date_of_birth)


def validate_date_joined_not_in_future(date_joined: date) -> None:
    validate_date_not_in_future(date_joined)