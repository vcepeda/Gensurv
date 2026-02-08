# gensurv_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as django_auth_views
from django.conf import settings
from django.conf.urls.static import static

# If you kept your custom password reset view in register/views.py
# (If you did NOT, remove this import and use django_auth_views.PasswordResetView below)
from register.views import CustomPasswordResetView


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Register
    path("", include("register.urls")),

    # Password reset
    path(
        "password_reset/",
        CustomPasswordResetView.as_view(template_name="registration/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        django_auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        django_auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        django_auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # API
    path("", include("gensurvapp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
