from apps.accounts.models import User

# Deliberately NOT the same shape as apps.teachers.permissions, despite
# looking like it could be:
#
# - CAN_VIEW_STAFF excludes TEACHER. Teacher's own directory being
#   visible to colleagues is reasonable collegial visibility; Staff
#   records (job title, employment type) are more of an HR-internal
#   concern that a Teacher has no particular need to browse.
#
# - CAN_MANAGE_STAFF is ADMIN-only, NOT [ADMIN, STAFF] the way
#   CAN_MANAGE_TEACHERS is [ADMIN, STAFF]. This project has one flat
#   STAFF role covering both HR-authorized staff AND rank-and-file staff
#   (security, maintenance, ...) - there's no finer-grained distinction
#   between them yet. Letting STAFF broadly manage OTHER staff records
#   would let, say, a groundskeeper edit a librarian's job title. The
#   self-service object-level check in views.py is what lets a staff
#   member touch THEIR OWN record instead.
CAN_VIEW_STAFF = [User.Role.ADMIN, User.Role.STAFF]
CAN_MANAGE_STAFF = [User.Role.ADMIN]
CAN_DEACTIVATE_STAFF = [User.Role.ADMIN]