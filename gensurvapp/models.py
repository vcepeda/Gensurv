from django.db import models
import os
from django.contrib.auth.models import User
from django.utils.text import slugify
import logging  # Ensure logging is imported
from django.conf import settings
from django import forms
from django.db.models.signals import post_delete
from django.dispatch import receiver



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



# Function to generate dynamic file paths
def user_submission_path(instance, filename):
    """
    Generate file path based on user and submission ID.
    Handles both Submission objects and related objects (e.g., UploadedFile).
    """
    # Check if the instance is Submission or related to Submission
    if isinstance(instance, Submission):  # For Submission objects
        submission_id = instance.pk if instance.pk else 'temp'
        username = slugify(instance.user.username)
    elif hasattr(instance, 'submission'):  # For related models like UploadedFile
        submission_id = instance.submission.pk if instance.submission.pk else 'temp'
        username = slugify(instance.submission.user.username)
    else:
        raise ValueError("Invalid instance passed to user_submission_path")

    # Return the dynamic path
    return os.path.join(
        'submissions',
        username,
        f'submission_{submission_id}',
        filename
    )


# Models
class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions'
    )
    metadata_file = models.FileField(upload_to=user_submission_path, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_bulk_upload = models.BooleanField(default=False)
    resubmission_allowed = models.BooleanField(default=False)
    metadata_warnings = models.TextField(blank=True, null=True)
    antibiotics_warnings = models.TextField(blank=True, null=True)
    fastq_warnings = models.TextField(blank=True, null=True)  # optional
    deletion_requested = models.BooleanField(default=False)
    upload_duration = models.FloatField(null=True, blank=True, help_text="Server processing time in seconds")
    client_total_upload_time = models.FloatField(null=True, blank=True, help_text="Client-reported total upload time in seconds")
    network_delay = models.FloatField(null=True, blank=True, help_text="Estimated network + upload delay in seconds")


    from django.core.files.base import ContentFile

    def save_files(self, metadata_file, cleaned_metadata_file, antibiotics_file=None, cleaned_antibiotics_file=None, fastq_files=None):
        """
        Save raw and cleaned versions of metadata and antibiotics, and any FASTQ files.
        """
        if metadata_file:
            SampleFile.objects.create(
                submission=self,
                sample_id="metadata",
                file_type='metadata_raw',
                file=metadata_file
            )

        if cleaned_metadata_file:
            SampleFile.objects.create(
                submission=self,
                sample_id="metadata",
                file_type='metadata_cleaned',
                file=cleaned_metadata_file
            )

        if antibiotics_file:
            SampleFile.objects.create(
                submission=self,
                sample_id="antibiotics",
                file_type='antibiotics_raw',
                file=antibiotics_file
            )

        if cleaned_antibiotics_file:
            SampleFile.objects.create(
                submission=self,
                sample_id="antibiotics",
                file_type='antibiotics_cleaned',
                file=cleaned_antibiotics_file
            )

        if fastq_files:
            for fastq_file in fastq_files:
                SampleFile.objects.create(
                    submission=self,
                    sample_id="fastq",
                    file_type='fastq',
                    file=fastq_file
                )



class SampleFile(models.Model):
    submission = models.ForeignKey(
        Submission, related_name='sample_files', on_delete=models.CASCADE
    )
    sample_id = models.CharField(max_length=100)
    file_type = models.CharField(max_length=30, choices=[
        ('metadata_raw', 'Metadata Raw'),
        ('metadata_cleaned', 'Metadata Cleaned'),
        ('antibiotics_raw', 'Antibiotics Raw'),
        ('antibiotics_cleaned', 'Antibiotics Cleaned'),
        ('fastq', 'FASTQ'),
    ])
    file = models.FileField(upload_to=user_submission_path)

    def __str__(self):
        return f"{self.file_type} for Sample {self.sample_id}"



class UploadedFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_submission_path)  # Updated to use `user_submission_path`
    cleaned_file = models.FileField(upload_to=user_submission_path, null=True, blank=True)  # Cleaned file (optional)
    file_type = models.CharField(max_length=30)
    sample_id = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.file_type} for {self.sample_id}"
    
class FileHistory(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file_type = models.CharField(max_length=30)  # metadata_raw, antibiotics,etc
    old_file = models.FileField(max_length=500)  # You assign full path yourself
    cleaned_file = models.FileField(null=True, blank=True, max_length=500)  # Same here
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} history for Submission {self.submission.id} at {self.timestamp}"




class AnalysisResult(models.Model):
    sample = models.OneToOneField(
        SampleFile,
        on_delete=models.CASCADE,
        related_name='analysis_result',
        limit_choices_to={'file_type': 'fastq'},
        null=True,  # Allow null values temporarily
        blank=True  # Allow blank values in forms
    )
    result_directory = models.CharField(max_length=255, default="not_set")  # Provide a default value
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], default='pending')
    
    completion_date = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Analysis for {self.sample.sample_id if self.sample else 'Unknown'} - {self.status}"


class BactopiaResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    sample_id = models.CharField(max_length=100)
    directory_path = models.TextField()  # Path to the Bactopia results directory

class PlasmidIdentResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    sample_id = models.CharField(max_length=100)
    directory_path = models.TextField()  # Path to the PlasmIDent results directory



