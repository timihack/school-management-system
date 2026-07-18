from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("students/", include("apps.students.urls")),
    path("parents/", include("apps.parents.urls")),
    path("departments/", include("apps.departments.urls")),
    path("teachers/", include("apps.teachers.urls")),
    path("staff/", include("apps.staff.urls")),
    path("", include("apps.dashboard.urls")),
]
