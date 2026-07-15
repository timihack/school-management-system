from django.conf import settings
from django.db import models


class Parent(models.Model):
    """
    Extends the custom User (role=PARENT) with parent-specific domain
    data, mirroring Student's design: identity fields stay on User,
    this model only adds what a User alone doesn't capture.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
    )
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # "students.Student" as a STRING reference, not an import - this is
    # the standard Django pattern for cross-app foreign keys. It avoids
    # apps/parents/models.py having to import apps/students/models.py at
    # module load time, which matters because Django resolves the app
    # registry lazily; a direct import here risks import-order issues if
    # the two apps ever needed to reference each other in both
    # directions. The string form defers resolution until Django's app
    # registry is fully loaded.
    students = models.ManyToManyField(
        "students.Student",
        through="Guardianship",
        related_name="guardians",
    )

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username


class Guardianship(models.Model):
  """
  The through-model for Parent <-> Student. Modeled explicitly (rather
  than a plain ManyToManyField with no through) because the
  relationship itself carries data: WHAT the relationship is (father/
  mother/guardian), WHO the school should contact first, and WHO is
  authorized to pick the child up. None of that fits on either Parent
  or Student alone - it belongs to the link between them.
  """

  class Relationship(models.TextChoices):
    FATHER = "FATHER", "Father"
    MOTHER = "MOTHER", "Mother"
    GUARDIAN = "GUARDIAN", "Guardian"
    OTHER = "OTHER", "Other"

  parent = models.ForeignKey(
    Parent, on_delete=models.CASCADE, related_name="guardianships"
  )
  student = models.ForeignKey(
    "students.Student", on_delete=models.CASCADE, related_name="guardianships"
  )
  relationship = models.CharField(max_length=20, choices=Relationship.choices)
  is_primary_contact = models.BooleanField(default=False)
  can_pickup = models.BooleanField(default=True)

  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(
        fields=["parent", "student"],
        name="unique_parent_student_guardianship",
      ),
      # Conditional constraint: at most ONE primary contact per
      # student, enforced by the database itself, not just
      # application code. services.link_guardianship() has to
      # clear any existing primary-contact flag BEFORE creating a
      # new one, precisely because this constraint would otherwise
      # reject the insert - the ordering there is load-bearing,
      # not a style choice.
      models.UniqueConstraint(
        fields=["student"],
        condition=models.Q(is_primary_contact=True),
        name="unique_primary_contact_per_student",
      ),
    ]

  def __str__(self) -> str:
      return f"{self.parent} - {self.student} ({self.relationship})"