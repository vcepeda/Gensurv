"""
URL configuration for gensurv_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as django_auth_views
from django.conf import settings
from django.conf.urls.static import static
# If you kept your custom password reset view in register/views.py
# (If you did NOT, remove this import and use django_auth_views.PasswordResetView below)
from register.views import CustomPasswordResetView  # Import the custom view

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Register
    path("", include("register.urls")),
    path('', include("django.contrib.auth.urls")),
    #hijack user
    path('hijack/', include('hijack.urls')),
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
    path("", include("gensurvapp.urls_nonapi")),
]
 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
