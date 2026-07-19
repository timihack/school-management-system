from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimestampedModel


class ClassLevel(TimestampedModel):
    """
    A stage in the school's academic ladder (e.g. "JSS1", "Primary 3",
    "Creche"). Like Department (Phase 7), this has no linked User of its
    own - it's a pure organizational concept, not a person.

    See docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md for the full domain
    requirements this model, ClassArm, ClassEnrollment, and
    PromotionPolicy below are built against.
    """

    class Category(models.TextChoices):
        PRE_CRECHE = "PRE_CRECHE", "Pre-Creche"
        CRECHE = "CRECHE", "Creche"
        KINDERGARTEN = "KINDERGARTEN", "Kindergarten"
        PRIMARY = "PRIMARY", "Primary"
        JUNIOR_SECONDARY = "JUNIOR_SECONDARY", "Junior Secondary"
        SENIOR_SECONDARY = "SENIOR_SECONDARY", "Senior Secondary"

    class AssessmentType(models.TextChoices):
        SCORE_BASED = "SCORE_BASED", "Score-based (CA + Exam)"
        SKILL_BASED = "SKILL_BASED", "Skill checklist (e.g. Creche/Nursery)"

    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    order = models.PositiveSmallIntegerField(
        unique=True,
        help_text=(
            "Sequence position across the WHOLE school ladder (e.g. 1 for "
            "the earliest level up to N for the last) - used to determine "
            "the normal 'next' level for promotion."
        ),
    )
    has_arms = models.BooleanField(
        default=False,
        help_text=(
            "Whether this level is split into arms (e.g. JSS1 A/B). "
            "Senior Secondary levels conventionally always set this True; "
            "Primary/Junior levels vary by school - see requirements doc "
            "Section 1."
        ),
    )
    assessment_type = models.CharField(
        max_length=20,
        choices=AssessmentType.choices,
        default=AssessmentType.SCORE_BASED,
    )

    # The NORMAL next level in sequence (e.g. JSS1 -> JSS2). Null for a
    # terminal level (e.g. SSS3, which graduates rather than promotes
    # further within the school). Self-referential, SET_NULL so deleting
    # a level doesn't cascade-delete whatever level used to follow it.
    promotes_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_from",
    )

    # True for the level whose EXIT is the special JSS3->SSS1-style
    # transition (arm placement across Science/Commerce/Arts/Technology)
    # rather than a simple move to `promotes_to`. See requirements doc
    # Section 4 - the actual placement WORKFLOW (gathering the cohort,
    # weighing preference/performance/admin judgment) is deferred to the
    # Examinations/Results phase; this flag only records the structural
    # fact for now, so Classes doesn't have to guess at that workflow's
    # shape before real term results exist to place students against.
    exit_requires_arm_placement = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.name


class ClassArm(TimestampedModel):
    """
    A specific group within a ClassLevel (e.g. "JSS1 A", or "SSS1
    Science"). Intended only for levels where has_arms=True - nothing in
    the database enforces that today; it's a soft rule enforced at the
    form/service layer, not a DB constraint. Revisit if real usage
    surfaces a case where that's insufficient.
    """

    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="arms")
    name = models.CharField(max_length=50, help_text="e.g. 'A', 'Science', 'Commerce'.")
    class_teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_arms_taught",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["class_level", "name"], name="unique_arm_name_per_level"
            )
        ]
        ordering = ["class_level__order", "name"]

    def __str__(self) -> str:
        return f"{self.class_level.name} {self.name}"


class ClassEnrollment(TimestampedModel):
    """
    WHERE a student currently is (and has been) in the class ladder.
    Modeled as its own history-preserving record - same reasoning as
    Guardianship (Phase 4): a bare 'current class' FK on Student would
    overwrite history every time a student moves, and requirements doc
    Sections 3/10 explicitly need repeat-tracking, which needs history
    to exist at all.

    "Current" enrollment is enforced the SAME WAY Guardianship enforces
    "one primary contact per student" - a conditional UniqueConstraint,
    not just application-level discipline.
    services.assign_student_to_class() clears the previous is_current
    flag BEFORE inserting the new one, for the same reason
    link_guardianship() does.
    """

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="class_enrollments"
    )
    # PROTECT, not SET_NULL: losing which class a student was in during
    # a past term is a more serious data loss than an unassigned
    # department (Phase 7) - deleting a ClassLevel that has ANY
    # enrollment history is blocked outright, forcing a deliberate data
    # decision instead of silently orphaning historical records.
    class_level = models.ForeignKey(
        ClassLevel, on_delete=models.PROTECT, related_name="enrollments"
    )
    class_arm = models.ForeignKey(
        ClassArm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )
    is_current = models.BooleanField(default=True)
    is_repeat = models.BooleanField(
        default=False,
        help_text="Whether this enrollment represents repeating the same level again.",
    )
    assigned_on = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_enrollments_assigned",
    )

    class Meta:
        ordering = ["-assigned_on"]
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(is_current=True),
                name="unique_current_enrollment_per_student",
            )
        ]

    def __str__(self) -> str:
        arm_part = f" {self.class_arm.name}" if self.class_arm else ""
        return f"{self.student} -> {self.class_level.name}{arm_part}"


class PromotionPolicy(TimestampedModel):
    """
    SKELETON ONLY - deliberately scoped to the fields that don't
    reference Subject, since Subject doesn't exist yet in this project's
    build order. See docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 9:
    gatekeeper SUBJECT selection (which subjects, e.g. Maths/English) is
    explicitly deferred to the Subjects/Examinations phases - the same
    way Student's Class FK and Teacher/Staff's Department FK were
    deferred until their target apps existed.

    Every ClassLevel gets exactly one PromotionPolicy, created with
    defaults the moment the level itself is created (see
    services.ensure_promotion_policy_exists) - so editing this in the UI
    is always an UPDATE, never a create-from-scratch.

    The two "mode" fields below (gatekeeper_pass_mark_mode,
    skill_based_promotion_mode) exist because the requirements doc
    confirmed schools genuinely need to CHOOSE BETWEEN approaches, not
    just tune a single number - see requirements doc Section 8's closing
    note on this pattern.
    """

    class PromotionBasis(models.TextChoices):
        THIRD_TERM_ONLY = "THIRD_TERM_ONLY", "Third term only"
        CUMULATIVE_ALL_TERMS = "CUMULATIVE_ALL_TERMS", "Cumulative (all terms)"

    class GatekeeperPassMarkMode(models.TextChoices):
        SAME_AS_OVERALL = "SAME_AS_OVERALL", "Same as overall pass percentage"
        CUSTOM = "CUSTOM", "Custom pass mark for gatekeeper subjects"

    class GatekeeperLogic(models.TextChoices):
        ANY_ONE_FAILS = "ANY_ONE_FAILS", "Failing ANY ONE gatekeeper subject forces a repeat"
        ALL_MUST_FAIL = "ALL_MUST_FAIL", "ALL gatekeeper subjects must be failed to force a repeat"

    class SkillBasedPromotionMode(models.TextChoices):
        AUTOMATIC = "AUTOMATIC", "Automatic (age/term-based, no criteria)"
        CHECKLIST_DERIVED = "CHECKLIST_DERIVED", "Derived from the skill checklist"
        ADMIN_JUDGMENT = "ADMIN_JUDGMENT", "Admin judgment call, no formula"

    class_level = models.OneToOneField(
        ClassLevel, on_delete=models.CASCADE, related_name="promotion_policy"
    )

    # --- Applies when class_level.assessment_type == SCORE_BASED ---
    pass_percentage = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall percentage required to be promoted.",
    )
    promotion_basis = models.CharField(
        max_length=25, choices=PromotionBasis.choices, default=PromotionBasis.THIRD_TERM_ONLY
    )
    gatekeeper_pass_mark_mode = models.CharField(
        max_length=20,
        choices=GatekeeperPassMarkMode.choices,
        default=GatekeeperPassMarkMode.SAME_AS_OVERALL,
    )
    gatekeeper_custom_pass_mark = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Only used when gatekeeper_pass_mark_mode is CUSTOM.",
    )
    gatekeeper_logic = models.CharField(
        max_length=20, choices=GatekeeperLogic.choices, default=GatekeeperLogic.ANY_ONE_FAILS
    )

    # --- Applies when class_level.assessment_type == SKILL_BASED ---
    skill_based_promotion_mode = models.CharField(
        max_length=20, choices=SkillBasedPromotionMode.choices, blank=True
    )

    def __str__(self) -> str:
        return f"Promotion policy for {self.class_level.name}"