import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.students.tests.factories import StudentFactory


def _make_test_image(*, format="JPEG", size_bytes_padding=0):
    """
    Builds a genuinely valid, tiny in-memory image - needed because
    Django's ImageField validates via Pillow's Image.verify() during
    full_clean(), not just by checking the file extension. A test that
    only faked the extension (e.g. renaming a text file to .jpg) would
    correctly get REJECTED by that validation, same as a real malicious
    upload would be - which is exactly the point of this being a
    layered defense, not just a naming convention.
    """
    buffer = io.BytesIO()
    image = Image.new("RGB", (10, 10), color="blue")
    image.save(buffer, format=format)
    content = buffer.getvalue() + (b"0" * size_bytes_padding)
    extension = "jpg" if format == "JPEG" else format.lower()
    return SimpleUploadedFile(f"photo.{extension}", content, content_type=f"image/{format.lower()}")


@pytest.mark.django_db
class TestStudentPhotoUpload:
    def test_admin_can_upload_a_valid_photo(self, client):
        admin = UserFactory(username="admin_photo1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()

        response = client.post(
            reverse("students:update", args=[student.pk]),
            {
                "gender": student.gender,
                "phone_number": "",
                "address": "",
                "photo": _make_test_image(),
            },
        )

        student.refresh_from_db()
        assert response.status_code == 302
        assert student.photo.name

    def test_non_image_file_disguised_with_an_image_extension_is_rejected(self, client):
        """
        The load-bearing security test: a plain text file renamed to
        .jpg is NOT a genuine image, and Django's ImageField calls
        Pillow's Image.verify() during validation - this must fail
        regardless of what extension the filename claims.
        """
        admin = UserFactory(username="admin_photo2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()
        fake_image = SimpleUploadedFile(
            "not_really_a_photo.jpg", b"this is definitely not image data", content_type="image/jpeg"
        )

        response = client.post(
            reverse("students:update", args=[student.pk]),
            {
                "gender": student.gender,
                "phone_number": "",
                "address": "",
                "photo": fake_image,
            },
        )

        student.refresh_from_db()
        assert response.status_code == 200  # form re-rendered with an error, not saved
        assert not student.photo

    def test_disallowed_extension_is_rejected(self, client):
        admin = UserFactory(username="admin_photo3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()
        pdf_file = SimpleUploadedFile("document.pdf", b"%PDF-1.4 fake pdf content", content_type="application/pdf")

        response = client.post(
            reverse("students:update", args=[student.pk]),
            {
                "gender": student.gender,
                "phone_number": "",
                "address": "",
                "photo": pdf_file,
            },
        )

        student.refresh_from_db()
        assert response.status_code == 200
        assert not student.photo

    def test_oversized_photo_is_rejected(self, client):
        admin = UserFactory(username="admin_photo4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()
        # Pad past the 2MB cap declared in validate_photo_file_size.
        oversized_image = _make_test_image(size_bytes_padding=3 * 1024 * 1024)

        response = client.post(
            reverse("students:update", args=[student.pk]),
            {
                "gender": student.gender,
                "phone_number": "",
                "address": "",
                "photo": oversized_image,
            },
        )

        student.refresh_from_db()
        assert response.status_code == 200
        assert not student.photo