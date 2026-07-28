"""
Upload service for COGDAT fastq-only submissions.

Unlike Gensurv/NUM-SAR, COGDAT uploads have no metadata file. The actual raw
FASTQ filename convention used by this archive is unknown, so this
deliberately does NOT try to guess a naming pattern or validate filenames
against the COGDAT sample roster (CogdatSampleId) - it just accepts whatever
is uploaded and stores it. Reconciling which file belongs to which sample is
a manual step to be done later; this is purely archival storage for a single
user's data, never sent to the analysis pipeline.
"""

import time
import logging

from django.db import transaction

from gensurvapp.models import Submission, UploadedFile

logger = logging.getLogger(__name__)


@transaction.atomic
def handle_cogdat_upload(*, user, fastq_files, dry_run=False):
    server_start = time.time()

    if not fastq_files:
        raise ValueError("At least one FASTQ file must be provided.")

    if dry_run:
        upload_duration = time.time() - server_start
        return {
            "submission_id": None,
            "resubmission_allowed": False,
            "message": f"Validation passed: {len(fastq_files)} file(s) ready to upload.",
            "upload_duration": upload_duration,
            "dry_run": True,
        }

    submission = Submission(user=user, is_bulk_upload=True)
    submission.submission_type = "cogdat"
    submission.submit_to_pipeline = False
    submission.save()

    for f in fastq_files:
        # Sample ID convention for this archive isn't known yet, so use the
        # full original filename as the label rather than guess where any
        # identifier starts/ends - whoever reconciles this later can re-map
        # it once the naming convention is confirmed.
        UploadedFile.objects.create(
            submission=submission,
            file=f,
            file_type="fastq",
            sample_id=f.name.strip()[:100],
        )

    upload_duration = time.time() - server_start

    try:
        from gensurvapp.services.global_stats_service import recompute_global_statistics
        recompute_global_statistics()
    except Exception as exc:
        logger.warning(f"Global statistics recompute failed after COGDAT upload: {exc}")

    return {
        "submission_id": submission.id,
        "resubmission_allowed": False,
        "message": f"COGDAT upload completed successfully: {len(fastq_files)} file(s) stored.",
        "upload_duration": upload_duration,
    }
