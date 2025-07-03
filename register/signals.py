from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def check_if_approved(sender, instance, created, **kwargs):
    if created:
        if not instance.is_approved:
            # You can send an email to the admin for approval, for example
            print(f"User {instance.username} requires approval.")
