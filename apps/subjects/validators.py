from django.core.exceptions import ValidationError


def validate_grade_band_does_not_overlap(
    *, grading_scale, min_percentage: int, max_percentage: int, exclude_pk: int | None = None
) -> None:
    """
    Checks a new/edited band's range against every OTHER band already
    under the same GradingScale. This needs to query siblings, which is
    exactly why it lives here as a standalone function (called from the
    form's clean()) rather than as a single-field model validator - it
    genuinely needs to see the rest of the scale's rows to do its job.
    """
    if min_percentage > max_percentage:
        raise ValidationError("Minimum percentage cannot be greater than maximum percentage.")

    siblings = grading_scale.bands.all()
    if exclude_pk is not None:
        siblings = siblings.exclude(pk=exclude_pk)

    for band in siblings:
        overlaps = min_percentage <= band.max_percentage and max_percentage >= band.min_percentage
        if overlaps:
            raise ValidationError(
                f"This range overlaps with existing band '{band.label}' "
                f"({band.min_percentage}-{band.max_percentage}%)."
            )