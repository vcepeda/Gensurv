from django.urls import path
from . import views

urlpatterns = [
    path("api/csrf/", views.api_csrf, name="api_csrf"),
    path("api/me/", views.api_me, name="api_me"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/login/", views.api_login, name="api_login"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("api/password-reset/", views.api_password_reset, name="api_password_reset"),
    path("api/password-reset/confirm/", views.api_password_reset_confirm, name="api_password_reset_confirm"),
]
