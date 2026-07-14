from apps.accounts.models import User

# Centralizes "who can do what" for the Students app specifically - one
# place to review or change access policy as requirements evolve,
# without hunting through every view in this file. core/permissions/
# provides the MECHANISM (RoleRequiredMixin); this file provides the
# POLICY (which roles) for this particular app.

CAN_VIEW_STUDENTS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_STUDENTS = [User.Role.ADMIN, User.Role.STAFF]
CAN_DEACTIVATE_STUDENTS = [User.Role.ADMIN]