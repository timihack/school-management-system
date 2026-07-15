from apps.accounts.models import User

CAN_VIEW_PARENTS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_PARENTS = [User.Role.ADMIN, User.Role.STAFF]
CAN_DEACTIVATE_PARENTS = [User.Role.ADMIN]