from .models import GradingScale


def ensure_grading_scale_exists(class_level) -> GradingScale:
    """
    Lazily creates a GradingScale for a class level on first access,
    rather than eagerly the moment a ClassLevel is created (the way
    Phase 8's ensure_promotion_policy_exists does for PromotionPolicy).

    Two reasons for the different approach here:
    1. Not every ClassLevel needs a grading scale at all - only
       SCORE_BASED ones do, and apps.classes has no reason to know that
       distinction belongs to grading.
    2. Doing this lazily means apps.classes.views (written in Phase 8)
       never needs to import or call into apps.subjects - keeping the
       dependency direction clean (subjects, built later, depends on
       classes; classes has zero awareness subjects exists).
    """
    grading_scale, _ = GradingScale.objects.get_or_create(class_level=class_level)
    return grading_scale