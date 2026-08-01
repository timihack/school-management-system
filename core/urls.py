from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("students/", include("apps.students.urls")),
    path("parents/", include("apps.parents.urls")),
    path("departments/", include("apps.departments.urls")),
    path("teachers/", include("apps.teachers.urls")),
    path("staff/", include("apps.staff.urls")),
    path("classes/", include("apps.classes.urls")),
    path("subjects/", include("apps.subjects.urls")),
    path("terms/", include("apps.terms.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("", include("apps.dashboard.urls")),
]

# Serves uploaded MEDIA files (e.g. student photos) in development only.
# This is the first feature needing it (Student.photo) - without this,
# files upload to MEDIA_ROOT successfully but have no URL to actually
# view them at all. In production, Django should NOT serve media files
# itself (no caching, no scalability) - that's Nginx's or an object
# store's (S3, etc.) job, set up separately when this goes to
# production, which is why this is guarded to DEBUG only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)