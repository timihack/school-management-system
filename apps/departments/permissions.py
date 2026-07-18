from apps.accounts.models import User

# CAN_MANAGE_DEPARTMENTS is Admin-only, not [ADMIN, STAFF] the way
# CAN_MANAGE_TEACHERS is. Creating/renaming organizational units and
# assigning department heads is a structural, org-chart-level decision -
# a different kind of stakes than the day-to-day people-management Staff
# already does for Teacher records.
CAN_VIEW_DEPARTMENTS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_DEPARTMENTS = [User.Role.ADMIN]