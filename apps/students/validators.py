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
      "Date of birth makes student older than 25 - please double check"
    )