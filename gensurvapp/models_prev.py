from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.conf import settings  # use settings to reference AUTH_USER_MODEL

class TodoItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="todoitem", null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Item(models.Model):
    todolist = models.ForeignKey(TodoItem, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return self.text

from django.db import models
import os
from django.utils.text import slugify
import logging  # Ensure you have this imported if you use logging

def user_submission_path(instance, filename):
    # Create a folder for each submission based on the user and submission ID
    if instance.pk:  # If the Submission has a primary key assigned
        return os.path.join(
            'submissions',
            slugify(instance.user.username),  # Folder based on the username
            f'submission_{instance.pk}',  # Folder for each submission
            filename  # The actual file name
        )
    # Use a temporary path if no primary key is available yet
    return os.path.join(
        'submissions',
        slugify(instance.user.username),
        'submission_temp',
        filename
    )

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    metadata_file = models.FileField(upload_to=user_submission_path)
    antibiotics_file = models.FileField(upload_to=user_submission_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Check if the submission already has an ID
        if not self.pk:
            super().save(*args, **kwargs)  # Save to get the ID assigned
            logging.debug(f"Assigned ID after initial save: {self.pk}")

        # Ensure file paths use the correct ID after getting the primary key
        new_metadata_path = user_submission_path(self, self.metadata_file.name)
        new_antibiotics_path = user_submission_path(self, self.antibiotics_file.name) if self.antibiotics_file else None

        # If the paths have changed, update them and save again
        if self.metadata_file.name != new_metadata_path:
            self.metadata_file.name = new_metadata_path
        if self.antibiotics_file and self.antibiotics_file.name != new_antibiotics_path:
            self.antibiotics_file.name = new_antibiotics_path

        # Save again to store correct paths
        super().save(*args, **kwargs)
        logging.debug(f"Saved with correct paths: {self.pk}")

class UploadedFile(models.Model):
    file = models.FileField(upload_to=user_submission_path)
    submission = models.ForeignKey(Submission, related_name='uploaded_fastq_files', on_delete=models.CASCADE)

    def __str__(self):
        return self.file.name



