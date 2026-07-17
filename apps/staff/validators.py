from datetime import date

from core.validators import validate_adult_employee_date_of_birth, validate_date_not_in_future


def validate_staff_date_of_birth(date_of_birth: date) -> None:
    validate_adult_employee_date_of_birth(date_of_birth)


def validate_date_joined_not_in_future(date_joined: date) -> None:
    validate_date_not_in_future(date_joined)