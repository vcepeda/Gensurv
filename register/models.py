from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add additional fields here
    name = models.CharField(max_length=100, blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    
    # Add the 'is_approved' field for admin approval
    is_approved = models.BooleanField(default=False)  # Default is False until admin approval
    
    class Meta:
        db_table = 'custom_user'

    # Fix for reverse accessor issue by adding related_name
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def save(self, *args, **kwargs):
        # Automatically approve and activate superusers
        if self.is_superuser:
            self.is_active = True
            self.is_approved = True
        super(CustomUser, self).save(*args, **kwargs)
