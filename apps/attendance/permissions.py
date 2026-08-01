from apps.accounts.models import User

# Broad viewing access for everyone who works day-to-day with students.
# Marking is different: Admin/Staff can mark ANY arm (front office
# covering for an absent teacher, or correcting records), while a
# Teacher can ONLY mark the arm(s) they are personally the class_teacher
# of - that second half is an OBJECT-level check (core.permissions.checks
# .check_role_or_owner), not expressible as a role list, since "which
# arms" varies per teacher.
CAN_VIEW_ATTENDANCE = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MARK_ATTENDANCE_BROADLY = [User.Role.ADMIN, User.Role.STAFF]