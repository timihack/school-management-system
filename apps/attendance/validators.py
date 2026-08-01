from django.core.exceptions import ValidationError


def validate_date_within_term(*, date, term) -> None:
    if date < term.start_date or date > term.end_date:
        raise ValidationError(
            f"{date} falls outside {term.get_name_display()} "
            f"({term.start_date} - {term.end_date})."
        )