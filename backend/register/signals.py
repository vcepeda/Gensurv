import logging
from pathlib import Path

from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify

from .models import CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def check_if_approved(sender, instance, created, **kwargs):
    if created:
        if not instance.is_approved:
            # You can send an email to the admin for approval, for example
            print(f"User {instance.username} requires approval.")


@receiver(pre_delete, sender=CustomUser)
def handle_user_hard_delete(sender, instance, **kwargs):
    username_slug = slugify(instance.username)
    submissions_root = Path(settings.MEDIA_ROOT) / "submissions"
    user_folder = submissions_root / username_slug

    if user_folder.exists() and user_folder.is_dir():
        target_folder = user_folder.with_name(f"{user_folder.name}_deleted")
        counter = 1
        while target_folder.exists():
            target_folder = user_folder.with_name(f"{user_folder.name}_deleted_{counter}")
            counter += 1

        try:
            user_folder.rename(target_folder)
            logger.info("Renamed submissions folder for deleted user '%s' to '%s'", instance.username, target_folder.name)
        except Exception:
            logger.exception("Failed to rename submissions folder for hard-deleted user '%s'", instance.username)

    # delete files when user deleted
    # Submission.objects.filter(user=instance).delete()
