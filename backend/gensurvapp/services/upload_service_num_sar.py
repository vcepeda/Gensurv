"""
Upload service for NUM-SAR submissions (num-sar_bacteria and num-sar_virus).

Kept separate from gensurvapp.services.upload_service because the NUM-SAR
metadata schema diverges substantially from the Gensurv schema:

  * Sample identifier column is LAB_SEQUENCE_ID (not "Sample Identifier").
  * Sequencing files are referenced by FILE_1_NAME / FILE_2_NAME (not the
    per-platform Illumina R1/R2, Nanopore, PacBio columns); the platform is
    described by the free-text SEQUENCING_PLATFORM field.
  * There is no antibiotics concept at all.

Validation of the metadata itself (schema, types, NUM-SAR-specific field
checks such as ISO dates and SHA256 sums) is handled by validate_and_save_csv,
which is told the submission_type so it applies the correct field validators.
"""

import time
import pandas as pd
from django.db import transaction

from gensurvapp.models import Submission, UploadedFile, AnalysisResult
from gensurvapp.services.global_stats_service import recompute_global_statistics
from gensurvapp.services.upload_service import normalize_submission_type
from gensurvapp.utils import validate_and_save_csv, generate_cleaned_file
from gensurvapp.num_sar_constants import (
    NUM_SAR_SUBMISSION_TYPES,
    NUM_SAR_METADATA_COLUMNS,
    NUM_SAR_ESSENTIAL_METADATA_COLUMNS,
)

import logging
logger = logging.getLogger(__name__)

# Lowercased to match the header-normalised DataFrame produced by
# validate_and_save_csv.
SAMPLE_ID_COLUMN = "lab_sequence_id"
FILE_1_COLUMN = "file_1_name"
FILE_2_COLUMN = "file_2_name"

VALID_FASTQ_EXTENSIONS = (
    ".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip",
)


def _safe_str(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def generate_statistics(metadata_df, submission_type):
    """
    Placeholder for the NUM-SAR metadata_statistics payload.

    Returns None for now; statistics generation will be implemented later.
    """
    return None


def _expected_files_for_row(row):
    """Return (file_1, file_2, [expected files]) for a metadata row."""
    file_1 = _safe_str(row.get(FILE_1_COLUMN))
    file_2 = _safe_str(row.get(FILE_2_COLUMN))
    expected = [f for f in (file_1, file_2) if f]
    return file_1, file_2, expected


def _validate_row_files(sample_id, file_1, file_2, expected_files, uploaded_names):
    """Apply the NUM-SAR file rules to a single metadata row."""
    if not file_1:
        raise ValueError(
            f"Sample '{sample_id}': FILE_1_NAME is required but missing."
        )

    if file_2 and not file_1:
        raise ValueError(
            f"Sample '{sample_id}': FILE_2_NAME provided without FILE_1_NAME."
        )

    for fname in expected_files:
        if not any(fname.lower().endswith(ext) for ext in VALID_FASTQ_EXTENSIONS):
            raise ValueError(
                f"Sample '{sample_id}': File '{fname}' has an invalid extension.\n"
                f"Allowed extensions: {', '.join(VALID_FASTQ_EXTENSIONS)}"
            )

    missing = [f for f in expected_files if f not in uploaded_names]
    if missing:
        raise ValueError(
            f"Sample '{sample_id}': Some sequencing files listed in metadata are missing from the upload.\n"
            f"Missing files: {', '.join(sorted(missing))}\n"
            f"Expected: {', '.join(expected_files)}"
        )


@transaction.atomic
def handle_single_upload(*, user, metadata_file, fastq_files, submission_type, submit_to_pipeline=False):

    server_start = time.time()

    submission_type = normalize_submission_type(submission_type)
    if submission_type not in NUM_SAR_SUBMISSION_TYPES:
        raise ValueError(
            f"handle_single_upload (NUM-SAR) called with non-NUM-SAR submission_type '{submission_type}'."
        )

    if not metadata_file:
        raise ValueError("Metadata file is required but not provided.")

    if not fastq_files:
        raise ValueError("At least one sequencing file must be provided.")

    logger.debug(f"Processing NUM-SAR metadata file: {metadata_file.name}")
    logger.debug(f"Processing {len(fastq_files)} uploaded sequencing file(s).")

    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(
        metadata_file,
        NUM_SAR_METADATA_COLUMNS,
        NUM_SAR_ESSENTIAL_METADATA_COLUMNS,
        submission_type=submission_type,
    )
    logger.debug(f"Detected delimiter (metadata): {detected_delimiter_meta}")

    if not valid_metadata:
        raise ValueError(f"FATAL:\n{metadata_message}")

    warning_message = None
    if metadata_warning:
        warning_message = f"Warnings in metadata file:\n{metadata_message}"
        logger.debug(f"Metadata file validated with warnings: {warning_message}")

    if metadata_df is None or metadata_df.empty:
        raise ValueError("Metadata file is empty or incorrectly formatted.")

    metadata_df.columns = metadata_df.columns.str.lower().str.strip()

    if SAMPLE_ID_COLUMN not in metadata_df.columns:
        raise ValueError(f"Metadata missing required column: '{SAMPLE_ID_COLUMN.upper()}'.")

    sample_ids = metadata_df[SAMPLE_ID_COLUMN].astype(str).str.strip()
    sample_ids = sample_ids[(sample_ids != "") & (sample_ids.str.lower() != "nan")]
    duplicates = sample_ids[sample_ids.str.lower().duplicated(keep=False)].unique()
    if len(duplicates) > 0:
        dup_str = ", ".join(sorted(duplicates, key=str.lower))
        raise ValueError(
            f"Duplicate {SAMPLE_ID_COLUMN.upper()} value(s) found in metadata file "
            f"'{metadata_file.name}': {dup_str}."
        )

    sample_id = _safe_str(metadata_df.loc[0, SAMPLE_ID_COLUMN])
    if not sample_id:
        raise ValueError(f"Metadata has missing/invalid '{SAMPLE_ID_COLUMN.upper()}' in first row.")

    uploaded_names = {f.name.strip() for f in fastq_files}
    logger.debug(f"Uploaded sequencing filenames: {uploaded_names}")

    file_1, file_2, expected_files = _expected_files_for_row(metadata_df.loc[0])
    _validate_row_files(sample_id, file_1, file_2, expected_files, uploaded_names)

    extra_fastq_warning = ""
    extra_files = uploaded_names - set(expected_files)
    if extra_files:
        extra_fastq_warning = (
            f"⚠️ Warning: Extra sequencing file(s) were uploaded but ignored: "
            f"{', '.join(sorted(extra_files))}."
        )
        logger.warning(extra_fastq_warning)

    logger.info(f"Sample '{sample_id}': All expected sequencing files validated successfully.")

    submission = Submission(user=user)
    submission.submission_type = submission_type
    submission.resubmission_allowed = bool(metadata_warning)
    if metadata_warning:
        submission.metadata_warnings = metadata_message
    if extra_files:
        submission.fastq_warnings = extra_fastq_warning
    submission.submit_to_pipeline = bool(submit_to_pipeline)
    stats = generate_statistics(metadata_df, submission_type)
    if stats is not None:
        submission.metadata_statistics = stats
    submission.save()

    for sid in sample_ids.tolist():
        AnalysisResult.objects.get_or_create(
            submission=submission,
            sample_id=sid,
            defaults={"status": "pending"},
        )

    cleaned_metadata_file = generate_cleaned_file(metadata_file.name, metadata_df)
    UploadedFile.objects.create(
        submission=submission,
        file=metadata_file,
        cleaned_file=cleaned_metadata_file,
        file_type="metadata_raw",
        sample_id=sample_id,
    )

    for expected_file in expected_files:
        matched_file = next(
            (f for f in fastq_files if f.name.strip() == expected_file.strip()),
            None,
        )
        if matched_file:
            UploadedFile.objects.create(
                submission=submission,
                file=matched_file,
                file_type="fastq",
                sample_id=sample_id,
            )
            logger.debug(f"Saved sequencing file: {matched_file.name}")

    message = "Single sample upload successful."
    if warning_message:
        message += f"\n{warning_message}"
    if extra_fastq_warning:
        message += f"\n{extra_fastq_warning}"

    upload_duration = time.time() - server_start

    try:
        recompute_global_statistics()
    except Exception as exc:
        logger.warning(f"Global statistics recompute failed after NUM-SAR single upload: {exc}")

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": message,
        "upload_duration": upload_duration,
    }


@transaction.atomic
def handle_bulk_upload(*, user, metadata_file, fastq_files, submission_type, submit_to_pipeline=False):

    server_start = time.time()

    submission_type = normalize_submission_type(submission_type)
    if submission_type not in NUM_SAR_SUBMISSION_TYPES:
        raise ValueError(
            f"handle_bulk_upload (NUM-SAR) called with non-NUM-SAR submission_type '{submission_type}'."
        )

    if not metadata_file:
        raise ValueError("Metadata file is required but not provided.")

    if not fastq_files:
        raise ValueError("At least one sequencing file must be provided.")

    logger.debug(f"Processing NUM-SAR bulk metadata file: {metadata_file.name}")
    logger.debug(f"Processing {len(fastq_files)} uploaded sequencing file(s).")

    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(
        metadata_file,
        NUM_SAR_METADATA_COLUMNS,
        NUM_SAR_ESSENTIAL_METADATA_COLUMNS,
        submission_type=submission_type,
    )
    logger.debug(f"Detected delimiter (metadata): {detected_delimiter_meta}")

    if not valid_metadata:
        raise ValueError(f"Metadata file error: {metadata_message}")

    metadata_warning_message = ""
    if metadata_warning:
        metadata_warning_message = f"{metadata_message}\n"
        logger.debug(f"Metadata file validated with warnings: {metadata_message}")

    if metadata_df is None or metadata_df.empty:
        raise ValueError("Metadata file is empty or incorrectly formatted.")

    metadata_df.columns = metadata_df.columns.str.lower().str.strip()

    if SAMPLE_ID_COLUMN not in metadata_df.columns:
        raise ValueError(f"Metadata missing required column: '{SAMPLE_ID_COLUMN.upper()}'.")

    metadata_df[SAMPLE_ID_COLUMN] = metadata_df[SAMPLE_ID_COLUMN].astype(str).str.strip()
    valid_sample_ids = metadata_df.loc[
        (metadata_df[SAMPLE_ID_COLUMN] != "")
        & (metadata_df[SAMPLE_ID_COLUMN].str.lower() != "nan"),
        SAMPLE_ID_COLUMN,
    ]
    duplicates = valid_sample_ids[valid_sample_ids.str.lower().duplicated(keep=False)].unique()
    if len(duplicates) > 0:
        dup_str = ", ".join(sorted(duplicates, key=str.lower))
        raise ValueError(
            f"Duplicate {SAMPLE_ID_COLUMN.upper()} value(s) found in metadata file "
            f"'{metadata_file.name}': {dup_str}."
        )

    uploaded_names = {f.name.strip() for f in fastq_files}
    logger.debug(f"Uploaded sequencing filenames: {uploaded_names}")

    matched_files = set()

    # Validation pass
    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get(SAMPLE_ID_COLUMN))
        if not sample_id:
            raise ValueError(f"Row {idx + 1}: Missing or invalid {SAMPLE_ID_COLUMN.upper()}.")

        file_1, file_2, expected_files = _expected_files_for_row(row)
        _validate_row_files(sample_id, file_1, file_2, expected_files, uploaded_names)
        matched_files.update(expected_files)
        logger.info(f"Sample '{sample_id}': All expected sequencing files validated successfully.")

    extra_fastq_warning_message = ""
    extra_files = uploaded_names - matched_files
    if extra_files:
        extra_fastq_warning_message = f"Extra sequencing file(s) ignored: {', '.join(sorted(extra_files))}\n"
        logger.warning(extra_fastq_warning_message.strip())

    submission = Submission(user=user, is_bulk_upload=True)
    submission.submission_type = submission_type
    submission.resubmission_allowed = bool(metadata_warning_message.strip())
    if metadata_warning_message.strip():
        submission.metadata_warnings = metadata_warning_message.strip()
    if extra_fastq_warning_message.strip():
        submission.fastq_warnings = extra_fastq_warning_message.strip()
    submission.submit_to_pipeline = bool(submit_to_pipeline)
    stats = generate_statistics(metadata_df, submission_type)
    if stats is not None:
        submission.metadata_statistics = stats
    submission.save()

    bulk_sample_ids = list(dict.fromkeys(valid_sample_ids.tolist()))
    for sid in bulk_sample_ids:
        AnalysisResult.objects.get_or_create(
            submission=submission,
            sample_id=sid,
            defaults={"status": "pending"},
        )

    cleaned_metadata_file = generate_cleaned_file(metadata_file.name, metadata_df)
    UploadedFile.objects.create(
        submission=submission,
        file=metadata_file,
        cleaned_file=cleaned_metadata_file,
        file_type="metadata_raw",
        sample_id="BULK",
    )

    # Save pass
    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get(SAMPLE_ID_COLUMN)) or f"row {idx + 1}"
        _, _, expected_files = _expected_files_for_row(row)

        for seq_filename in expected_files:
            matched_file = next(
                (f for f in fastq_files if f.name.strip() == seq_filename.strip()),
                None,
            )
            if matched_file:
                matched_file.seek(0)
                UploadedFile.objects.create(
                    submission=submission,
                    file=matched_file,
                    file_type="fastq",
                    sample_id=sample_id,
                )
            else:
                logger.warning(f"Skipping missing sequencing file: {seq_filename} for sample '{sample_id}'")

    success_messages = ["Bulk upload completed successfully."]
    if metadata_warning_message.strip():
        success_messages.append("⚠️ Metadata file accepted with warnings.")
    if extra_fastq_warning_message.strip():
        success_messages.append("⚠️ Extra sequencing files were ignored.")

    bulk_success_message = "\n".join(success_messages)

    upload_duration = time.time() - server_start

    try:
        recompute_global_statistics()
    except Exception as exc:
        logger.warning(f"Global statistics recompute failed after NUM-SAR bulk upload: {exc}")

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": bulk_success_message,
        "upload_duration": upload_duration,
    }