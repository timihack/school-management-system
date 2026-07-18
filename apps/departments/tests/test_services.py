import pytest

from apps.departments.services import delete_department
from apps.departments.tests.factories import DepartmentFactory
from apps.staff.tests.factories import StaffFactory
from apps.teachers.tests.factories import TeacherFactory


@pytest.mark.django_db
class TestDeleteDepartment:
    def test_deleting_unassigns_teachers_and_staff_rather_than_deleting_them(self):
        department = DepartmentFactory()
        teacher = TeacherFactory(department=department)
        staff = StaffFactory(department=department)

        result = delete_department(department)

        teacher.refresh_from_db()
        staff.refresh_from_db()

        assert result == {"teacher_count": 1, "staff_count": 1}
        assert teacher.department is None
        assert staff.department is None
        # The people themselves must still exist - SET_NULL, not CASCADE.
        assert teacher.pk is not None
        assert staff.pk is not None

    def test_counts_are_zero_for_an_empty_department(self):
        department = DepartmentFactory()

        result = delete_department(department)

        assert result == {"teacher_count": 0, "staff_count": 0}