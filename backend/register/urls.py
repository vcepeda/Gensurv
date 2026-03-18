from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("api/csrf/", views.api_csrf, name="api_csrf"),
    path("api/me/", views.api_me, name="api_me"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/login/", views.api_login, name="api_login"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("register/", RedirectView.as_view(url="/"), name="register"),
]