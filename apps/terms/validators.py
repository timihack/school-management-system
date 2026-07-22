from django.core.exceptions import ValidationError


def validate_start_before_end(start_date, end_date) -> None:
    if start_date and end_date and start_date >= end_date:
        raise ValidationError("Start date must be before end date.")


def validate_term_within_session(*, term_start, term_end, session) -> None:
    if term_start and term_start < session.start_date:
        raise ValidationError("Term cannot start before its academic session starts.")
    if term_end and term_end > session.end_date:
        raise ValidationError("Term cannot end after its academic session ends.")