from django.core.exceptions import ValidationError

from .models import ClassLevel, PromotionPolicy


def validate_promotion_policy_consistency(
    *,
    class_level: ClassLevel,
    gatekeeper_pass_mark_mode: str,
    gatekeeper_custom_pass_mark,
    skill_based_promotion_mode: str,
) -> None:
    """
    Cross-field consistency rules for PromotionPolicy that no single
    field's own validators can express. Kept as a standalone function
    (not a model.clean() override) per this project's established
    validators.py convention - see apps/students/validators.py and
    apps/teachers/validators.py for the same pattern.
    """
    if (
        gatekeeper_pass_mark_mode == PromotionPolicy.GatekeeperPassMarkMode.CUSTOM
        and gatekeeper_custom_pass_mark is None
    ):
        raise ValidationError(
            "A custom gatekeeper pass mark is required when the mode is set to Custom."
        )

    if (
        class_level.assessment_type == ClassLevel.AssessmentType.SKILL_BASED
        and not skill_based_promotion_mode
    ):
        raise ValidationError(
            "A skill-based promotion mode is required for skill-based class levels."
        )

    if (
        class_level.assessment_type == ClassLevel.AssessmentType.SCORE_BASED
        and skill_based_promotion_mode
    ):
        raise ValidationError(
            "Skill-based promotion mode should be left blank for score-based class levels."
        )