from apps.terms.selectors import get_current_term


def current_term(request):
    """
    Makes `current_term` available in every template's context (topbar,
    dashboards, etc.) without every view function needing to fetch and
    pass it individually - the same mechanism Django's own
    'django.contrib.auth.context_processors.auth' uses to make `user`
    available everywhere. Returns None gracefully if no term has been
    activated yet.
    """
    return {"current_term": get_current_term()}