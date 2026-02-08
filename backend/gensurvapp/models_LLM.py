# gensurvapp/models.py
from __future__ import annotations

import os
from django.db import models
from django.utils.text import slugify
from django.conf import settings


# -----------------------------
# Upload path helper
# -----------------------------
def user_submission_path(instance, filename: str) -> str:
    """
    Dynamic storage path:
      submissions/<username>/submission_<id>/<filename>

    Works for:
      - Submission
      - UploadedFile / PipelineResult / FileHistory (anything with .submission)
    """
    if isinstance(instance, Submission):
        submission_id = instance.pk if instance.pk else "temp"
        username = slugify(instance.user.username)
    elif hasattr(instance, "submission") and instance.submission:
        submission_id = instance.submission.pk if instance.submission.pk else "temp"
        username = slugify(instance.submission.user.username)
    else:
        raise ValueError("Invalid instance passed to user_submission_path")

    return os.path.join("submissions", username, f"submission_{submission_id}", filename)


# -----------------------------
# Core models
# -----------------------------
class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # flags / workflow
    is_bulk_upload = models.BooleanField(default=False)
    resubmission_allowed = models.BooleanField(default=False)
    deletion_requested = models.BooleanField(default=False)

    # warnings (string blobs you already use)
    metadata_warnings = models.TextField(blank=True, null=True)
    antibiotics_warnings = models.TextField(blank=True, null=True)
    fastq_warnings = models.TextField(blank=True, null=True)

    # timing metrics
    upload_duration = models.FloatField(
        null=True, blank=True, help_text="Server processing time in seconds"
    )
    client_total_upload_time = models.FloatField(
        null=True, blank=True, help_text="Client-reported total upload time in seconds"
    )
    network_delay = models.FloatField(
        null=True, blank=True, help_text="Estimated network + upload delay in seconds"
    )

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Submission {self.id} ({self.user})"


class UploadedFile(models.Model):
    """
    Single source of truth for ALL uploaded files:
      - metadata_raw / metadata_cleaned
      - antibiotics_raw / antibiotics_cleaned
      - fastq

    sample_id:
      - single upload: you may store the sample id from metadata for all relevant rows
      - bulk upload: sample_id distinguishes per-sample files
    """

    class FileType(models.TextChoices):
        METADATA_RAW = "metadata_raw", "Metadata Raw"
        METADATA_CLEANED = "metadata_cleaned", "Metadata Cleaned"
        ANTIBIOTICS_RAW = "antibiotics_raw", "Antibiotics Raw"
        ANTIBIOTICS_CLEANED = "antibiotics_cleaned", "Antibiotics Cleaned"
        FASTQ = "fastq", "FASTQ"

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="files",
    )

    file_type = models.CharField(max_length=30, choices=FileType.choices)

    # For metadata rows you can use:
    # - "metadata" (or empty) for single upload
    # For fastq/antibiotics in bulk, this is real sample_id.
    sample_id = models.CharField(max_length=100, blank=True, default="")

    file = models.FileField(upload_to=user_submission_path)
    cleaned_file = models.FileField(
        upload_to=user_submission_path, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "file_type"]),
            models.Index(fields=["submission", "sample_id"]),
            models.Index(fields=["file_type"]),
        ]
        # Optional (recommended) constraints:
        # - only one metadata_raw per submission
        # - only one metadata_cleaned per submission
        # This prevents accidental duplicates and simplifies dashboard queries.
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "file_type"],
                condition=models.Q(file_type="metadata_raw"),
                name="uniq_metadata_raw_per_submission",
            ),
            models.UniqueConstraint(
                fields=["submission", "file_type"],
                condition=models.Q(file_type="metadata_cleaned"),
                name="uniq_metadata_cleaned_per_submission",
            ),
        ]

    def __str__(self) -> str:
        sid = self.sample_id or "no-sample"
        return f"{self.file_type} ({sid}) for Submission {self.submission_id}"


class FileHistory(models.Model):
    """
    Resubmission history.
    Store paths as text (more robust than FileField if you're writing your own paths).
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)

    file_type = models.CharField(max_length=30)  # e.g. metadata_raw, antibiotics_raw
    old_file_path = models.CharField(max_length=500)
    cleaned_file_path = models.CharField(max_length=500, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "file_type"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.file_type} history for Submission {self.submission_id} at {self.timestamp}"


# -----------------------------
# Unified pipeline results
# -----------------------------
class PipelineResult(models.Model):
    """
    One unified table for all pipeline outputs per sample.

    Replaces:
      - AnalysisResult
      - BactopiaResult
      - PlasmidIdentResult
    """

    class Pipeline(models.TextChoices):
        BACTOPIA = "bactopia", "Bactopia"
        PLASMIDENT = "plasmident", "PlasmIDent"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="pipeline_results",
    )
    sample_id = models.CharField(max_length=100)

    pipeline = models.CharField(max_length=30, choices=Pipeline.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    directory_path = models.TextField(blank=True, null=True)

    completion_date = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "sample_id"]),
            models.Index(fields=["pipeline", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "sample_id", "pipeline"],
                name="uniq_pipeline_result_per_sample",
            )
        ]

    def __str__(self) -> str:
        return f"{self.pipeline} {self.sample_id} ({self.status}) - Submission {self.submission_id}"
