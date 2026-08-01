from datetime import date

from django.core.exceptions import ValidationError


def validate_date_of_birth_is_plausible(date_of_birth: date) -> None:
    """
    Basic sanity check: a school student should reasonably be between 0
    and 25 years old at admission. Prevents obvious data-entry mistakes
    (typos, wrong century) without hard-coding a rigid age policy the
    school might want to configure differently later.
    """
    today = date.today()

    if date_of_birth > today:
        raise ValidationError("Date of birth cannot be in the future.")

    age_years = (today - date_of_birth).days / 365.25
    if age_years > 25:
        raise ValidationError(
            "Date of birth makes this student older than 25 - please double check."
        )


def validate_photo_file_size(uploaded_file) -> None:
    """
    Caps a profile photo at 2MB. Django has no built-in max-size
    validator for FileField/ImageField, so this is written by hand.

    This is ONE of three layers protecting the photo upload, not the
    only one - see Student.photo's own field definition for the other
    two: a FileExtensionValidator (rejects anything not jpg/jpeg/png/webp
    by extension) and, more importantly, Django's ImageField itself
    calls Pillow's Image.verify() during full_clean() - a file renamed
    to look like a photo but that isn't a genuine, parseable image
    (e.g. a script renamed to .jpg) fails THAT check regardless of what
    this function does. Extension-checking alone is never sufficient on
    its own; the Pillow verification is what actually matters most here.
    """
    max_size_bytes = 2 * 1024 * 1024  # 2MB
    if uploaded_file.size > max_size_bytes:
        raise ValidationError("Photo must be 2MB or smaller.")