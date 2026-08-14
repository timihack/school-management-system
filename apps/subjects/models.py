from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.classes.models import ClassLevel
from core.models import TimestampedModel


class Subject(TimestampedModel):
    """
    A subject taught at one or more class levels (e.g. Mathematics taught
    across JSS1-SSS3). assessment_type is a PRIMARY MODE HINT (used for
    sensible defaults and to inform the level's promotion policy), NOT a
    hard gate: a subject can have AssessmentComponents, SkillChecklistItems,
    or both simultaneously - confirmed by a real report card (AOS
    Montessori) showing early-years domains with BOTH a numeric CA/Exam/
    Total row AND a skill checklist underneath it. A school wanting the
    same subject NAME to genuinely mean two different things at
    different levels (e.g. skill-only "Numeracy" at Creche vs
    numeric-only "Mathematics" at Primary) can still create two separate
    Subject rows - nothing here forces combining them.

    is_active exists (unlike Department, which has none) because a
    Subject participates in ongoing assessment records that must be
    historically preserved even after the subject stops being offered -
    same reasoning as Student/Teacher/Staff's soft-delete, not
    Department's hard-delete.
    """

    class ComputationMethod(models.TextChoices):
        SUM_COMPONENTS = "SUM_COMPONENTS", "Sum components (CA total + Exam total)"
        AVERAGE_CA_AND_EXAM = (
            "AVERAGE_CA_AND_EXAM",
            "Average CA components, average with Exam components",
        )

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True, help_text="e.g. 'MTH', 'ENG'.")
    assessment_type = models.CharField(
        max_length=20,
        choices=ClassLevel.AssessmentType.choices,
        default=ClassLevel.AssessmentType.SCORE_BASED,
        help_text=(
            "Primary mode hint for defaults and grading policy - does NOT "
            "prevent this subject from having both numeric components and "
            "a skill checklist at the same time."
        ),
    )
    computation_method = models.CharField(
        max_length=25,
        choices=ComputationMethod.choices,
        default=ComputationMethod.SUM_COMPONENTS,
        help_text=(
            "How CA and Exam components combine into a final score. "
            "SUM_COMPONENTS: sum all CA component maxes + sum all Exam "
            "component maxes (e.g. CA=40 + Exam=60 = 100 - confirmed real "
            "usage: AOS Montessori). AVERAGE_CA_AND_EXAM: average the CA "
            "components together, average the Exam components together, "
            "then average those two averages (confirmed real usage: Elon "
            "College's T1/T2/T3 averaged, then averaged with the Term "
            "Exam). The actual per-student computation using this setting "
            "is implemented in the Examinations phase, once real scores "
            "exist to combine - this field only records the CHOICE."
        ),
    )
    class_levels = models.ManyToManyField(
        ClassLevel, related_name="subjects", blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def ca_max_total(self) -> int:
        """
        Sum of all CA-type component max scores, regardless of
        computation_method - this is always a factually accurate figure
        (e.g. "there are 3 CA components each maxing 100"), even for
        AVERAGE_CA_AND_EXAM subjects where the actual combination formula
        averages rather than sums them. 0 if none defined yet.
        """
        return (
            self.assessment_components.filter(
                component_type=AssessmentComponent.ComponentType.CA
            ).aggregate(total=models.Sum("max_score"))["total"]
            or 0
        )

    @property
    def exam_max_total(self) -> int:
        return (
            self.assessment_components.filter(
                component_type=AssessmentComponent.ComponentType.EXAM
            ).aggregate(total=models.Sum("max_score"))["total"]
            or 0
        )

    @property
    def overall_max_score(self) -> int:
        """
        The 'out of' denominator for this subject - used by the overall
        promotion percentage formula confirmed in
        docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 3 (sum of actual
        scores / SUM OF MAX across all a student's subjects). Different
        subjects can legitimately have different totals here - that's
        exactly why that formula divides by a summed max, not a flat 100
        per subject.
        """
        return self.ca_max_total + self.exam_max_total


class AssessmentComponent(TimestampedModel):
    """
    ONE scoring component for a SCORE-BASED subject (e.g. "CA1" worth
    10, "CA2" worth 10, "CA3" worth 20, "Exam" worth 60). The number of
    components and their individual max scores are fully configurable
    per subject, per docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 5 -
    some schools use just one CA, others CA1-CA3; the split (e.g.
    CA=40/Exam=60) can differ per subject too. component_type lets
    Subject.ca_max_total/exam_max_total compute the CA-vs-Exam split
    without any string-matching on component names.
    """

    class ComponentType(models.TextChoices):
        CA = "CA", "Continuous Assessment"
        EXAM = "EXAM", "Exam"

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="assessment_components"
    )
    name = models.CharField(max_length=50, help_text="e.g. 'CA1', 'CA2', 'Exam'.")
    component_type = models.CharField(max_length=10, choices=ComponentType.choices)
    max_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "name"], name="unique_component_name_per_subject"
            )
        ]
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return f"{self.subject.name} - {self.name} ({self.max_score})"


class SkillChecklistItem(TimestampedModel):
    """
    ONE discrete skill for a SKILL-BASED subject (e.g. under "Numerical":
    "Write 1 to 10", "Read 1 to 20"). Assessed later (Examinations phase)
    as achieved / not-yet-achieved per student per term - this model
    only defines WHAT the checklist items are, not any student's actual
    assessment against them. Deliberately NOT a numeric score - see
    docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 6: this is a
    genuinely different assessment paradigm, not a scaled-down version of
    AssessmentComponent.
    """

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="skill_items")
    description = models.CharField(max_length=200, help_text="e.g. 'Can identify 5 colors'.")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.description


class GradingScale(TimestampedModel):
    """
    Scoped to exactly one ClassLevel - confirmed in
    docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 7 that grading
    scales differ by level (e.g. simpler A-F for Junior, WAEC-style
    A1-F9 for Senior), NOT school-wide and NOT per-subject. Unlike
    PromotionPolicy (Phase 8), this is NOT auto-created for every
    ClassLevel the moment it's made - only SCORE_BASED levels need one
    at all, and creating it lazily (on first access, via
    services.ensure_grading_scale_exists) avoids apps.classes needing
    any awareness that apps.subjects exists, keeping the dependency
    direction clean (later apps depend on earlier ones, not the
    reverse).
    """

    class_level = models.OneToOneField(
        ClassLevel, on_delete=models.CASCADE, related_name="grading_scale"
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="e.g. 'WAEC 9-point scale', optional."
    )

    def __str__(self) -> str:
        return self.name or f"Grading scale for {self.class_level.name}"


class GradeBand(TimestampedModel):
    """
    One boundary+label row within a GradingScale (e.g. "A1", 75-100).
    Bounds are PERCENTAGE points (0-100), not raw scores - deliberate,
    since different subjects can have different max totals (see
    Subject.overall_max_score), so only a normalized percentage scale
    makes sense as a single per-level grading scale.
    """

    grading_scale = models.ForeignKey(GradingScale, on_delete=models.CASCADE, related_name="bands")
    label = models.CharField(max_length=10, help_text="e.g. 'A1', 'B2', 'A', 'F9'.")
    description = models.CharField(max_length=50, blank=True, help_text="e.g. 'Excellent'.")
    min_percentage = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_percentage = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        ordering = ["-min_percentage"]

    def __str__(self) -> str:
        return f"{self.label} ({self.min_percentage}-{self.max_percentage}%)"


class Topic(TimestampedModel):
    """
    One syllabus item within a Subject's curriculum, scoped to a
    specific ClassLevel (e.g. "Fractions" under Mathematics, JSS1).
    Deliberately NOT a new Django app - reuses Subject, ClassLevel, and
    Term rather than duplicating any relationship-modeling, the same
    reasoning that kept GradingScale/GradeBand inside apps.subjects
    instead of spinning up a separate app for them.

    class_level is REQUIRED (unlike term) because a topic's syllabus
    placement is level-specific by definition - "Fractions" as taught
    in JSS1 is a genuinely different curriculum entry from "Fractions"
    in JSS2, even under the same Subject. term is OPTIONAL (SET_NULL)
    because not every school wants to pin a topic to a specific term
    up front - some build out a level-wide syllabus first and schedule
    it into terms later, or never, if they only track subject/level
    granularity. SET_NULL (not CASCADE) so deleting a Term never
    silently deletes curriculum content - it just un-schedules it.

    Uses a STRING FK reference ("terms.Term") rather than a direct
    import, per the project's established deferred cross-app FK
    pattern (see docs/ARCHITECTURE_DECISIONS.md): apps.subjects (Phase
    9) predates apps.terms (Phase 10) in the build order, so this keeps
    the dependency direction honest even though both apps now exist by
    the time this field is being added.

    Curriculum management deliberately has BROADER RBAC than Subject
    structural management itself (Admin+Staff+Teacher, vs. Subject's
    Admin-only - see permissions.CAN_MANAGE_TOPICS) - confirmed by the
    user as the foundation the future Timetable and AI curriculum-tutor
    features will ground themselves against.
    """

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    class_level = models.ForeignKey(
        ClassLevel, on_delete=models.CASCADE, related_name="topics"
    )
    term = models.ForeignKey(
        "terms.Term",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="topics",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "class_level", "name"],
                name="unique_topic_name_per_subject_level",
            )
        ]
        ordering = ["class_level__order", "subject__name", "order"]

    def __str__(self) -> str:
        return f"{self.subject.name} - {self.name} ({self.class_level.name})"