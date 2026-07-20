from apps.accounts.models import User

# Curriculum-structural decisions (creating subjects, defining assessment
# components/skill items, setting grading scales) are Admin-only - same
# reasoning as Departments and Classes. Teachers need to SEE subjects
# (they'll enter scores against them once Examinations exists), so they
#'re admitted to the view-only policy.
CAN_VIEW_SUBJECTS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_SUBJECTS = [User.Role.ADMIN]
CAN_MANAGE_GRADING_SCALE = [User.Role.ADMIN]