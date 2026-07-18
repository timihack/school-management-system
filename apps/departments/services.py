from .models import Department


def delete_department(department: Department) -> dict:
    """
    A REAL delete, not soft - see models.py for why. Teacher.department
    and Staff.department both use on_delete=SET_NULL, so members aren't
    cascade-deleted - they're unassigned. Returns counts so the view can
    tell whoever deleted it what just changed for those people.

    No @transaction.atomic here: unlike create_student()/create_teacher()/
    etc., which span TWO models (User + Profile) and need atomicity to
    avoid a half-created state, this is a single delete() call plus two
    read-only counts taken beforehand - there's nothing to roll back
    partway through.
    """
    teacher_count = department.teacher_set.count()
    staff_count = department.staff_set.count()
    department.delete()
    return {"teacher_count": teacher_count, "staff_count": staff_count}