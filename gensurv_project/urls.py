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
from register import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from gensurvapp import views as app_views  # Import views from gensurvapp
from register.views import CustomPasswordResetView  # Import the custom view

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin site URLs
    #path('register/', include('register.urls')),  # Include app-level URLs for 'register'
    path('register/', auth_views.register, name="register"),
    path('login/', auth_views.login_view, name="login"),
    path('logout/', auth_views.logout_view, name='logout'),  # Direct link to logout view
    path('', include("django.contrib.auth.urls")),
    # Password reset URLs
    #path('password_reset/', django_auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    #path('password_reset/done/', django_auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    #path('reset/<uidb64>/<token>/', django_auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    #path('reset/done/', django_auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('password_reset/', CustomPasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password_reset/done/', django_auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', django_auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', django_auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('', include('gensurvapp.urls')),
]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
