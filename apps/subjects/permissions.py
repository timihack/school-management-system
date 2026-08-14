from apps.accounts.models import User

# Curriculum-structural decisions (creating subjects, defining assessment
# components/skill items, setting grading scales) are Admin-only - same
# reasoning as Departments and Classes. Teachers need to SEE subjects
# (they'll enter scores against them once Examinations exists), so they
#'re admitted to the view-only policy.
CAN_VIEW_SUBJECTS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]
CAN_MANAGE_SUBJECTS = [User.Role.ADMIN]
CAN_MANAGE_GRADING_SCALE = [User.Role.ADMIN]

# Curriculum (Topic) management is DELIBERATELY broader than Subject
# structural management - confirmed directly by the user ("curriculum
# by teacher, staff or school admin"). Day-to-day content curation
# (what topics exist, what order they're taught in) is a different kind
# of decision from structural/administrative changes to a Subject
# itself (its assessment components, grading scale, whether it exists
# at all) - Admin+Staff+Teacher can all manage Topics, but only Admin
# can manage the Subject those Topics belong to.
#
# This is currently role-only, not owner-scoped: any Teacher can edit
# any subject's curriculum, not just subjects they actually teach,
# because no "teacher teaches subject X" assignment concept exists yet
# (that's Timetable's job - Phase 13). Flagged as a natural future
# check_role_or_owner candidate once Timetable exists, not a bug today.
CAN_MANAGE_TOPICS = [User.Role.ADMIN, User.Role.STAFF, User.Role.TEACHER]