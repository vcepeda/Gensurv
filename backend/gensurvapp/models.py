from django.db import models
import os
from django.utils.text import slugify
from django.conf import settings


def user_submission_path(instance, filename):
    """
    submissions/<username>/submission_<id>/<filename>

    Works for Submission and any model with a .submission FK.
    """
    if isinstance(instance, Submission):
        submission_id = instance.pk if instance.pk else "temp"
        username = slugify(instance.user.username)
    elif hasattr(instance, "submission") and instance.submission:
        submission_id = instance.submission.pk if instance.submission.pk else "temp"
        username = slugify(instance.submission.user.username)
    else:
        raise ValueError("Invalid instance passed to user_submission_path")

    return os.path.join(
        "submissions",
        username,
        f"submission_{submission_id}",
        filename,
    )


class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_bulk_upload = models.BooleanField(default=False)
    resubmission_allowed = models.BooleanField(default=False)
    deletion_requested = models.BooleanField(default=False)
    submit_to_pipeline = models.BooleanField(default=False)

    metadata_warnings = models.TextField(blank=True, null=True)
    antibiotics_warnings = models.TextField(blank=True, null=True)
    fastq_warnings = models.TextField(blank=True, null=True)

    upload_duration = models.FloatField(null=True, blank=True)
    client_total_upload_time = models.FloatField(null=True, blank=True)
    network_delay = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Submission {self.id} ({self.user})"


class UploadedFile(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="files",
    )

    file = models.FileField(upload_to=user_submission_path)
    cleaned_file = models.FileField(
        upload_to=user_submission_path,
        null=True,
        blank=True,
    )

    # file_type = models.CharField(max_length=30) 
    file_type = models.CharField(max_length=30, choices=[
        ('metadata_raw', 'Metadata Raw'),
        ('metadata_cleaned', 'Metadata Cleaned'),
        ('antibiotics_raw', 'Antibiotics Raw'),
        ('antibiotics_cleaned', 'Antibiotics Cleaned'),
        ('fastq', 'FASTQ'),
    ])
    sample_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    def __str__(self):
        return f"{self.file_type} for {self.sample_id or 'no-sample'}"


class FileHistory(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file_type = models.CharField(max_length=30)

    # storing paths explicitly (as you already do)
    old_file = models.FileField(max_length=500)
    cleaned_file = models.FileField(
        null=True,
        blank=True,
        max_length=500,
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} history for Submission {self.submission.id}"


class AnalysisResult(models.Model):
    sample_id = models.CharField(max_length=100)

    result_directory = models.CharField(max_length=255, default="not_set")
    status = models.CharField(max_length=20)  # NO choices

    completion_date = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Analysis for {self.sample_id} - {self.status}"


class BactopiaResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    sample_id = models.CharField(max_length=100)
    directory_path = models.TextField()


class PlasmidIdentResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    sample_id = models.CharField(max_length=100)
    directory_path = models.TextField()