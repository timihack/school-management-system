import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_photo_file_size


def _student_photo_upload_path(instance, filename: str) -> str:
    """
    Generates a random, non-guessable filename rather than using the
    student's admission number or original filename directly. Two
    reasons: (1) predictable paths (e.g. "student_photos/ELC-24-001.jpg")
    would let someone enumerate/guess other students' photo URLs by
    admission number pattern, and (2) reusing the original uploaded
    filename verbatim risks path-traversal-style tricks or filename
    collisions between students. The original extension is preserved
    (already validated by FileExtensionValidator below) so the file
    still opens correctly.
    """
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"student_photos/{uuid.uuid4().hex}.{extension}"


class Student(models.Model):
    """
    Extends the custom User (role=STUDENT) with student-specific domain
    data. Identity fields (name, email, login credentials) stay on User -
    this model never duplicates them, only adds what a User alone
    doesn't capture.

    NOTE: no FK to a "class"/"grade" yet - the Classes app doesn't exist
    yet (it comes later in the module order). Adding that FK now would
    mean guessing at a schema we haven't designed. It gets added via a
    migration on THIS model once the Classes app exists, which is the
    normal, expected way schemas evolve - not a shortcut being taken now.
    """

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        # OTHER = "OTHER", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    admission_number = models.CharField(max_length=20, unique=True, db_index=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    admission_date = models.DateField()
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    # First real file upload in the project. Three independent layers
    # of validation, none sufficient alone:
    # 1. FileExtensionValidator - rejects by extension immediately.
    # 2. Django's ImageField itself calls Pillow's Image.verify() during
    #    full_clean() - the load-bearing check. A file renamed to LOOK
    #    like a photo but that isn't a genuine, parseable image fails
    #    here regardless of what its extension claims.
    # 3. validate_photo_file_size - caps upload size at 2MB.
    photo = models.ImageField(
        upload_to=_student_photo_upload_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_photo_file_size,
        ],
        help_text="JPG, PNG, or WebP - max 2MB.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["admission_number"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} ({self.admission_number})"