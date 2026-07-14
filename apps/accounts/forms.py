from django.contrib.auth.forms import AuthenticationForm


class StyledAuthenticationForm(AuthenticationForm):
    """
    Wraps Django's built-in AuthenticationForm purely to attach Tailwind
    utility classes to the rendered widgets. All validation logic
    (credential checking, inactive-user rejection, etc.) stays exactly
    as Django implements it - we only touch presentation here.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_classes = (
            "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm "
            "focus:outline-none focus:ring-2 focus:ring-indigo-500"
        )
        self.fields["username"].widget.attrs.update(
            {"class": field_classes, "placeholder": "Username", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"class": field_classes, "placeholder": "Password"}
        )
 