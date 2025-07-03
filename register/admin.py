from django.contrib import admin
from .models import CustomUser  # Use your custom user model if applicable
from django.core.mail import send_mail
from django.conf import settings

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'institution', 'is_active', 'is_approved')
    list_filter = ('is_active', 'is_approved')
    search_fields = ('username', 'email', 'institution')

    def save_model(self, request, obj, form, change):
        # If the user is being approved, send the notification email
        if change and 'is_approved' in form.changed_data and obj.is_approved:
            site_url = settings.SITE_URL #in settings.py
            # Send an email to the user
            send_mail(
                'Your Account Has Been Approved',
                'Congratulations, your account has been approved by the admin. You can now log in by clicking the link below:\n\n'
                f'{site_url}/login/',  # Replace with the actual login URL
                'GenSurv Admin Team <admin@gensurv.de>',  # Custom name and email in 'From'
                #settings.DEFAULT_FROM_EMAIL,
                [obj.email],
                fail_silently=False,
            )

            # Optionally, send an email to the admin
            send_mail(
                'User Account Approved',
                f'The user {obj.username} ({obj.email}) has been approved.',
                'GenSurv Admin Team <admin@gensurv.de>',  # Custom name and email in 'From'
                #settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )

        # Continue with the usual save process
        super().save_model(request, obj, form, change)