from apps.accounts.models import User

# Creating sessions/terms and activating a term are structural,
# calendar-defining decisions with system-wide consequences (a future
# Promote action gates on "is this the current, final term") - Admin-only,
# same reasoning as Departments and Classes. Everyone who works day-to-day
# needs to SEE which term is current, hence the broader view policy.
CAN_VIEW_TERMS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_TERMS = [User.Role.ADMIN]