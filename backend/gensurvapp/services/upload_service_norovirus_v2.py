"""Upload and conversion service for user-facing Norovirus V2 metadata."""

import os
import time

import pandas as pd
from django.core.files.base import ContentFile
from django.db import transaction

from gensurvapp.models import AnalysisResult, Submission, UploadedFile
from gensurvapp.norovirus_v2_constants import (
    NOROVIRUS_RKI_CONVERSION_ENABLED,
    NOROVIRUS_V2_ESSENTIAL_COLUMNS,
    NOROVIRUS_V2_METADATA_COLUMNS,
)
from gensurvapp.services.norovirus_v2_conversion import (
    build_num_sar_metadata,
)
from gensurvapp.services.norovirus_v2_validation import (
    validate_norovirus_v2_fields,
)
from gensurvapp.utils import generate_cleaned_file, validate_and_save_csv


SAMPLE_ID_COLUMN = "lab_sequence_id"
SEQUENCING_FILE_COLUMNS = ("illumina r1", "illumina r2", "nanopore", "pacbio")
PRIMARY_SEQUENCING_FILE_COLUMNS = ("illumina r1", "nanopore", "pacbio")
VALID_SEQUENCING_EXTENSIONS = (
    ".fastq",
    ".fq",
    ".bam",
    ".fastq.gz",
    ".fq.gz",
    ".bam.gz",
    ".bz2",
    ".xz",
    ".zip",
)


def _safe_str(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _validate_sample_ids(metadata_df):
    if SAMPLE_ID_COLUMN not in metadata_df.columns:
        raise ValueError("Metadata missing required column: 'LAB_SEQUENCE_ID'.")

    sample_ids = metadata_df[SAMPLE_ID_COLUMN].map(_safe_str)
    missing_rows = sample_ids[sample_ids.isna()].index + 1
    if len(missing_rows):
        raise ValueError(
            "Missing or invalid LAB_SEQUENCE_ID in row(s): "
            + ", ".join(map(str, missing_rows))
        )

    duplicate_mask = sample_ids.str.lower().duplicated(keep=False)
    if duplicate_mask.any():
        duplicates = sorted(sample_ids[duplicate_mask].unique(), key=str.lower)
        raise ValueError(
            "Duplicate LAB_SEQUENCE_ID value(s): " + ", ".join(duplicates)
        )


def _validate_sequencing_files(metadata_df, fastq_files):
    uploaded_names = {
        os.path.basename(uploaded.name.strip())
        for uploaded in fastq_files
    }
    referenced_names = set()
    errors = []

    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get(SAMPLE_ID_COLUMN)) or f"row {idx + 1}"
        filenames = {
            column: _safe_str(row.get(column))
            for column in SEQUENCING_FILE_COLUMNS
        }

        if not any(filenames[column] for column in PRIMARY_SEQUENCING_FILE_COLUMNS):
            errors.append(
                f"Sample '{sample_id}': At least one of Illumina R1, Nanopore, "
                "or PacBio must be provided."
            )

        if filenames["illumina r2"] and not filenames["illumina r1"]:
            errors.append(
                f"Sample '{sample_id}': Illumina R2 cannot be provided without Illumina R1."
            )

        expected_names = [name for name in filenames.values() if name]
        referenced_names.update(expected_names)

        invalid_extensions = [
            name
            for name in expected_names
            if not name.lower().endswith(VALID_SEQUENCING_EXTENSIONS)
        ]
        if invalid_extensions:
            errors.append(
                f"Sample '{sample_id}': Invalid sequencing file extension: "
                + ", ".join(invalid_extensions)
            )

        missing_names = sorted(set(expected_names) - uploaded_names)
        if missing_names:
            errors.append(
                f"Sample '{sample_id}': Referenced sequencing file(s) were not uploaded: "
                + ", ".join(missing_names)
            )

    if errors:
        raise ValueError("\n".join(errors))

    return sorted(uploaded_names - referenced_names)


def validate_upload(*, metadata_file, fastq_files, max_rows=None):
    """Validate V2 metadata and its uploaded sequencing files without writing data."""
    if not metadata_file:
        raise ValueError("Metadata file is required but not provided.")
    if not fastq_files:
        raise ValueError("At least one sequencing file must be provided.")

    valid, warning, message, delimiter, metadata_df = validate_and_save_csv(
        metadata_file,
        NOROVIRUS_V2_METADATA_COLUMNS,
        NOROVIRUS_V2_ESSENTIAL_COLUMNS,
        submission_type="norovirus_v2",
        max_rows=max_rows,
    )
    if not valid:
        raise ValueError(message)
    if metadata_df is None or metadata_df.empty:
        raise ValueError("Metadata file is empty or incorrectly formatted.")

    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
    _validate_sample_ids(metadata_df)
    validate_norovirus_v2_fields(metadata_df)
    extra_files = _validate_sequencing_files(metadata_df, fastq_files)
    conversion_enabled = NOROVIRUS_RKI_CONVERSION_ENABLED
    converted_metadata_df = None
    if conversion_enabled:
        converted_metadata_df = build_num_sar_metadata(metadata_df, fastq_files)

    messages = ["Validation passed: metadata and file names look correct."]
    if warning and message:
        messages.append(message)
    if extra_files:
        messages.append(
            "Extra sequencing file(s) were uploaded but are not referenced: "
            + ", ".join(extra_files)
        )
    if not conversion_enabled:
        messages.append("RKI/NUM-SAR conversion is currently disabled.")

    return {
        "metadata_df": metadata_df,
        "converted_metadata_df": converted_metadata_df,
        "conversion_enabled": conversion_enabled,
        "delimiter": delimiter,
        "has_warnings": bool(warning or extra_files),
        "message": "\n".join(messages),
    }


def _converted_metadata_file(original_name, converted_metadata_df):
    name_root = os.path.splitext(os.path.basename(original_name))[0]
    converted_file = ContentFile(converted_metadata_df.to_csv(index=False))
    converted_file.name = f"converted_num_sar_{name_root}.csv"
    return converted_file


def _persist_upload(
    *,
    user,
    metadata_file,
    fastq_files,
    validation_result,
    is_bulk_upload,
    submit_to_pipeline,
):
    metadata_df = validation_result["metadata_df"]
    converted_metadata_df = validation_result["converted_metadata_df"]
    sample_ids = metadata_df[SAMPLE_ID_COLUMN].map(_safe_str).tolist()

    submission = Submission.objects.create(
        user=user,
        is_bulk_upload=is_bulk_upload,
        submission_type="num-sar_norovirus",
        submit_to_pipeline=bool(submit_to_pipeline),
        resubmission_allowed=validation_result["has_warnings"],
        metadata_warnings=(
            validation_result["message"] if validation_result["has_warnings"] else None
        ),
    )

    for sample_id in sample_ids:
        AnalysisResult.objects.get_or_create(
            submission=submission,
            sample_id=sample_id,
            defaults={"status": "pending"},
        )

    cleaned_metadata_file = generate_cleaned_file(metadata_file.name, metadata_df)
    metadata_file.seek(0)
    UploadedFile.objects.create(
        submission=submission,
        file=metadata_file,
        cleaned_file=cleaned_metadata_file,
        file_type="metadata_raw",
        sample_id="BULK" if is_bulk_upload else sample_ids[0],
    )

    if converted_metadata_df is not None:
        UploadedFile.objects.create(
            submission=submission,
            file=_converted_metadata_file(metadata_file.name, converted_metadata_df),
            file_type="metadata_converted",
            sample_id="BULK" if is_bulk_upload else sample_ids[0],
        )

    uploaded_by_name = {
        os.path.basename(uploaded.name.strip()): uploaded
        for uploaded in fastq_files
    }
    for _, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get(SAMPLE_ID_COLUMN))
        for column in SEQUENCING_FILE_COLUMNS:
            filename = _safe_str(row.get(column))
            if not filename:
                continue
            uploaded = uploaded_by_name[filename]
            uploaded.seek(0)
            UploadedFile.objects.create(
                submission=submission,
                file=uploaded,
                file_type="fastq",
                sample_id=sample_id,
            )

    return submission


@transaction.atomic
def handle_single_upload(
    *,
    user,
    metadata_file,
    fastq_files,
    submit_to_pipeline=False,
    dry_run=False,
    **kwargs,
):
    """Validate, convert, and optionally persist a single-sample upload."""
    server_start = time.time()
    result = validate_upload(
        metadata_file=metadata_file,
        fastq_files=fastq_files,
        max_rows=1,
    )
    if dry_run:
        return {
            "submission_id": None,
            "resubmission_allowed": result["has_warnings"],
            "message": result["message"],
            "upload_duration": time.time() - server_start,
            "dry_run": True,
        }

    submission = _persist_upload(
        user=user,
        metadata_file=metadata_file,
        fastq_files=fastq_files,
        validation_result=result,
        is_bulk_upload=False,
        submit_to_pipeline=submit_to_pipeline,
    )
    return {
        "submission_id": submission.id,
        "resubmission_allowed": result["has_warnings"],
        "message": "Single Norovirus V2 upload completed successfully.",
        "upload_duration": time.time() - server_start,
        "dry_run": False,
    }


@transaction.atomic
def handle_bulk_upload(
    *,
    user,
    metadata_file,
    fastq_files,
    submit_to_pipeline=False,
    dry_run=False,
    **kwargs,
):
    """Validate, convert, and optionally persist a bulk upload."""
    server_start = time.time()
    result = validate_upload(metadata_file=metadata_file, fastq_files=fastq_files)
    if dry_run:
        return {
            "submission_id": None,
            "resubmission_allowed": result["has_warnings"],
            "message": result["message"],
            "upload_duration": time.time() - server_start,
            "dry_run": True,
        }

    submission = _persist_upload(
        user=user,
        metadata_file=metadata_file,
        fastq_files=fastq_files,
        validation_result=result,
        is_bulk_upload=True,
        submit_to_pipeline=submit_to_pipeline,
    )
    return {
        "submission_id": submission.id,
        "resubmission_allowed": result["has_warnings"],
        "message": "Bulk Norovirus V2 upload completed successfully.",
        "upload_duration": time.time() - server_start,
        "dry_run": False,
    }
