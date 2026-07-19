from apps.accounts.models import User

# Structural, org-chart-level decisions (creating/editing levels & arms,
# setting promotion policy) are Admin-only - same reasoning as
# Departments (Phase 7). Day-to-day student class assignment is more
# operational, so Staff is admitted there too - matching how Staff can
# manage Students/Parents/Teachers records generally elsewhere in this
# project.
CAN_VIEW_CLASSES = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_CLASSES = [User.Role.ADMIN]
CAN_MANAGE_ENROLLMENT = [User.Role.ADMIN, User.Role.STAFF]
CAN_MANAGE_PROMOTION_POLICY = [User.Role.ADMIN]