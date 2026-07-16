from apps.accounts.models import User

CAN_VIEW_TEACHERS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_TEACHERS = [User.Role.ADMIN, User.Role.STAFF]
CAN_DEACTIVATE_TEACHERS = [User.Role.ADMIN]