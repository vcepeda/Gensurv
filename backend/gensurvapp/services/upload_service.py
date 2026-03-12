import time
import re
import math
import pandas as pd
from django.db import transaction

from gensurvapp.models import Submission, UploadedFile
from gensurvapp.services.global_stats_service import recompute_global_statistics
from gensurvapp.utils import validate_and_save_csv, generate_cleaned_file
from gensurvapp.constants import METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS, ANTIBIOTICS_COLUMNS

import logging
logger = logging.getLogger(__name__)

def normalize_submission_type(value):
    if not value:
        return "bacteria"
    normalized = str(value).strip().lower()
    if normalized not in ("bacteria", "virus"):
        raise ValueError("Invalid submission_type. Use 'bacteria' or 'virus'.")
    return normalized


def generate_statistics(metadata_df, submission_type, antibiotics_dfs=None):
    antibiotics_dfs = antibiotics_dfs or []

    def _json_safe(value):
        if isinstance(value, dict):
            return {k: _json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value

    if metadata_df is None or metadata_df.empty:
        return {
            "submission_type": submission_type,
            "total_rows": 0,
            "illumina_r1_only_count": 0,
            "illumina_r1_r2_count": 0,
            "nanopore_count": 0,
            "pacbio_count": 0,
            "unique_isolate_species_count": 0,
            "unique_sample_identifiers": 0,
            "duplicate_sample_identifiers": [],
            "missing_sample_identifier_count": 0,
            "platform_file_presence": {
                "illumina_r1": 0,
                "illumina_r2": 0,
                "nanopore": 0,
                "pacbio": 0,
            },
            "antibiotics": {
                "rows_with_antibiotics_file": 0,
                "rows_with_antibiotics_info": 0,
                "rows_with_both": 0,
                "different_antibiotics_count": 0,
                "sir_type_count": 0,
                "sir_counts": {
                    "resistant": 0,
                    "intermediate": 0,
                    "susceptible": 0,
                },
                "mic_column_present": False,
                "mic_numeric_count": 0,
                "mic_numeric_values": [],
            },
        }

    stats_df = metadata_df.copy()
    stats_df.columns = stats_df.columns.str.lower().str.strip()

    def _is_present(value):
        if pd.isna(value):
            return False
        value_str = str(value).strip()
        return bool(value_str) and value_str.lower() != "nan"

    if "sample identifier" in stats_df.columns:
        sample_series = stats_df["sample identifier"].astype(str).str.strip()
        valid_sample_series = sample_series[
            (sample_series != "") & (sample_series.str.lower() != "nan")
        ]
        duplicate_samples = sorted(
            valid_sample_series[
                valid_sample_series.str.lower().duplicated(keep=False)
            ].unique(),
            key=str.lower,
        )
        missing_sample_identifier_count = int(len(sample_series) - len(valid_sample_series))
        unique_sample_identifiers = int(valid_sample_series.str.lower().nunique())
    else:
        duplicate_samples = []
        missing_sample_identifier_count = int(len(stats_df.index))
        unique_sample_identifiers = 0

    def _count_present(column_name):
        if column_name not in stats_df.columns:
            return 0
        return int(stats_df[column_name].apply(_is_present).sum())

    rows_with_antibiotics_file = _count_present("antibiotics file")
    rows_with_antibiotics_info = _count_present("antibiotics info")

    illumina_r1_present = (
        stats_df["illumina r1"].apply(_is_present)
        if "illumina r1" in stats_df.columns
        else pd.Series(False, index=stats_df.index)
    )
    illumina_r2_present = (
        stats_df["illumina r2"].apply(_is_present)
        if "illumina r2" in stats_df.columns
        else pd.Series(False, index=stats_df.index)
    )

    illumina_r1_r2_count = int((illumina_r1_present & illumina_r2_present).sum())
    illumina_r1_only_count = int((illumina_r1_present & ~illumina_r2_present).sum())

    isolate_species_series = (
        stats_df["isolate species"].astype(str).str.strip()
        if "isolate species" in stats_df.columns
        else pd.Series(dtype=str)
    )
    valid_isolate_species = isolate_species_series[
        (isolate_species_series != "") & (isolate_species_series.str.lower() != "nan")
    ]
    unique_isolate_species_count = int(valid_isolate_species.str.lower().nunique())

    rows_with_both = 0
    if "antibiotics file" in stats_df.columns and "antibiotics info" in stats_df.columns:
        rows_with_both = int(
            (
                stats_df["antibiotics file"].apply(_is_present)
                & stats_df["antibiotics info"].apply(_is_present)
            ).sum()
        )

    different_antibiotics_count = 0
    sir_counts = {
        "resistant": 0,
        "intermediate": 0,
        "susceptible": 0,
    }
    mic_column_present = False
    mic_numeric_values = []

    def _extract_numeric_mic(value):
        if value is None or pd.isna(value):
            return None

        value_str = str(value).strip()
        if not value_str or value_str.lower() == "nan":
            return None

        value_str = value_str.replace(",", ".")
        match = re.search(r"[-+]?\d*\.?\d+", value_str)
        if not match:
            return None

        try:
            parsed = float(match.group(0))
            if not math.isfinite(parsed):
                return None
            return parsed
        except (TypeError, ValueError):
            return None

    antibiotic_frames = [
        frame.copy()
        for frame in antibiotics_dfs
        if frame is not None and not frame.empty
    ]

    if antibiotic_frames:
        antibiotics_stats_df = pd.concat(antibiotic_frames, ignore_index=True)
        antibiotics_stats_df.columns = antibiotics_stats_df.columns.str.lower().str.strip()

        if "tested antibiotic" in antibiotics_stats_df.columns:
            tested_series = antibiotics_stats_df["tested antibiotic"].astype(str).str.strip()
            tested_series = tested_series[
                (tested_series != "") & (tested_series.str.lower() != "nan")
            ]
            different_antibiotics_count = int(tested_series.str.lower().nunique())

        sir_column = None
        if "observed antibiotic resistance sir" in antibiotics_stats_df.columns:
            sir_column = "observed antibiotic resistance sir"
        elif "sir" in antibiotics_stats_df.columns:
            sir_column = "sir"

        if sir_column:
            sir_series = antibiotics_stats_df[sir_column].astype(str).str.strip()

            for value in sir_series:
                value_lower = value.lower()
                if not value or value_lower == "nan":
                    continue
                if value_lower in ("r", "resistant"):
                    sir_counts["resistant"] += 1
                elif value_lower in ("i", "intermediate"):
                    sir_counts["intermediate"] += 1
                elif value_lower in ("s", "susceptible"):
                    sir_counts["susceptible"] += 1

        mic_columns = [column for column in antibiotics_stats_df.columns if "mic" in column.lower()]
        if mic_columns:
            mic_column_present = True
            extracted_mic_values = []
            for mic_column in mic_columns:
                raw_mic_series = antibiotics_stats_df[mic_column]
                extracted_mic_values.extend([
                    parsed
                    for parsed in raw_mic_series.map(_extract_numeric_mic).tolist()
                    if parsed is not None
                ])
            mic_numeric_values = extracted_mic_values

    sir_type_count = int(sum(1 for key in ("resistant", "intermediate", "susceptible") if sir_counts[key] > 0))

    stats_payload = {
        "submission_type": submission_type,
        "total_rows": int(len(stats_df.index)),
        "illumina_r1_only_count": illumina_r1_only_count,
        "illumina_r1_r2_count": illumina_r1_r2_count,
        "nanopore_count": _count_present("nanopore"),
        "pacbio_count": _count_present("pacbio"),
        "unique_isolate_species_count": unique_isolate_species_count,
        "unique_sample_identifiers": unique_sample_identifiers,
        "duplicate_sample_identifiers": duplicate_samples,
        "missing_sample_identifier_count": missing_sample_identifier_count,
        "platform_file_presence": {
            "illumina_r1": _count_present("illumina r1"),
            "illumina_r2": _count_present("illumina r2"),
            "nanopore": _count_present("nanopore"),
            "pacbio": _count_present("pacbio"),
        },
        "antibiotics": {
            "rows_with_antibiotics_file": rows_with_antibiotics_file,
            "rows_with_antibiotics_info": rows_with_antibiotics_info,
            "rows_with_both": rows_with_both,
            "different_antibiotics_count": different_antibiotics_count,
            "sir_type_count": sir_type_count,
            "sir_counts": sir_counts,
            "mic_column_present": mic_column_present,
            "mic_numeric_count": len(mic_numeric_values),
            "mic_numeric_values": mic_numeric_values,
        },
    }

    return _json_safe(stats_payload)



@transaction.atomic
def handle_single_upload(*, user, metadata_file, uploaded_antibiotics_file, fastq_files, submission_type, submit_to_pipeline=False):

    server_start = time.time()

    warning_message = None
    extra_fastq_warning = ""
    antibiotics_message = None

    submission_type = normalize_submission_type(submission_type)

    if submission_type == "virus" and uploaded_antibiotics_file:
        raise ValueError("Virus submissions do not accept antibiotics files.")

    if not metadata_file:
        raise ValueError("Metadata file is required but not provided.")
    logger.debug(f"Processing uploaded metadata file: {metadata_file.name} (type: {type(metadata_file)})")

    if uploaded_antibiotics_file:
        logger.debug(f"Processing uploaded antibiotics file: {uploaded_antibiotics_file.name} (type: {type(uploaded_antibiotics_file)})")
    else:
        logger.debug("No antibiotics file uploaded.")

    if not fastq_files:
        raise ValueError("At least one sequencing file must be provided.")

    logger.debug(f"Processing {len(fastq_files)} uploaded FASTQ files.")
    for i, fastq_file in enumerate(fastq_files):
        logger.debug(f"Processing #{i+1} uploaded FASTQ file: {fastq_file.name} (type: {type(fastq_file)})")

    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(
        metadata_file,
        METADATA_COLUMNS,
        ESSENTIAL_METADATA_COLUMNS
    )
    logger.debug(f"Detected delimiter (metadata): {detected_delimiter_meta}")

    if not valid_metadata:
        raise ValueError(f"FATAL:\n{metadata_message}")

    if metadata_warning:
        warning_message = f"Warnings in metadata file:\n{metadata_message}"
        logger.debug(f"Metadata file validated with warnings: {warning_message}")
    else:
        logger.debug(f"Metadata file validated successfully: {metadata_file.name}")

    if metadata_df is None or metadata_df.empty:
        raise ValueError("Metadata file is empty or incorrectly formatted.")

    # normalize headers
    metadata_df.columns = metadata_df.columns.str.lower().str.strip()

    def _safe_str(x):
        if x is None:
            return None
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return None
        return s
    

    # sample id
    if "sample identifier" not in metadata_df.columns:
        raise ValueError("Metadata missing required column: 'sample identifier'.")

    single_sample_ids = (
        metadata_df["sample identifier"]
        .astype(str)
        .str.strip()
    )
    single_sample_ids = single_sample_ids[
        (single_sample_ids != "") & (single_sample_ids.str.lower() != "nan")
    ]
    duplicate_single_sample_ids = single_sample_ids[
        single_sample_ids.str.lower().duplicated(keep=False)
    ].unique()
    if len(duplicate_single_sample_ids) > 0:
        duplicates = ", ".join(sorted(duplicate_single_sample_ids, key=str.lower))
        raise ValueError(
            f"Duplicate sample identifier(s) found in metadata file '{metadata_file.name}': {duplicates}. "
        )

    sample_id = str(metadata_df.loc[0, "sample identifier"]).strip()
    if not sample_id or sample_id.lower() == "nan":
        raise ValueError("Metadata has missing/invalid 'sample identifier' in first row.")
    
    if submission_type == "virus":
        ab_file_val = _safe_str(metadata_df.loc[0, "antibiotics file"]) if "antibiotics file" in metadata_df.columns else None
        ab_info_val = _safe_str(metadata_df.loc[0, "antibiotics info"]) if "antibiotics info" in metadata_df.columns else None
        if ab_file_val or ab_info_val:
            raise ValueError(f"Sample '{sample_id}': Virus submissions must not include antibiotics fields.")

    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")

    uploaded_fastq_files_names = {f.name.strip() for f in fastq_files}
    logger.debug(f"Uploaded FASTQ filenames: {uploaded_fastq_files_names}")

    def _get_meta_filename(col):
        return (
            str(metadata_df.loc[0, col]).strip()
            if col in metadata_df.columns and pd.notna(metadata_df.loc[0, col])
            else None
        )

    illumina_r1 = _get_meta_filename("illumina r1")
    illumina_r2 = _get_meta_filename("illumina r2")
    nanopore = _get_meta_filename("nanopore")
    pacbio = _get_meta_filename("pacbio")

    expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]

    logger.debug("Checking sequencing files listed in metadata:")
    logger.debug(f"• Illumina R1: {illumina_r1 or 'None'}")
    logger.debug(f"• Illumina R2: {illumina_r2 or 'None'}")
    logger.debug(f"• Nanopore: {nanopore or 'None'}")
    logger.debug(f"• PacBio: {pacbio or 'None'}")
    logger.debug(f"Final list of expected FASTQ files: {expected_fastq_files}")

    if not any([illumina_r1, nanopore, pacbio]):
        raise ValueError(
            f"Sample '{sample_id}': At least one sequencing platform file must be provided "
            f"(Illumina R1, Nanopore, or PacBio)."
        )

    if illumina_r2 and not illumina_r1:
        raise ValueError(f"Sample '{sample_id}': Illumina R2 file provided without Illumina R1.")

    for fname in expected_fastq_files:
        if not any(fname.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(
                f"Sample '{sample_id}': File '{fname}' has an invalid extension.\n"
                f"Allowed extensions: {', '.join(valid_extensions)}"
            )
        logger.debug(f"File '{fname}' passed extension check.")

    missing_fastq_files = set(expected_fastq_files) - uploaded_fastq_files_names
    if missing_fastq_files:
        raise ValueError(
            f"Sample '{sample_id}': Some FASTQ files listed in metadata are missing from the upload.\n"
            f"Missing files: {', '.join(sorted(missing_fastq_files))}\n"
            f"Expected: {', '.join(expected_fastq_files)}\n"
            f"Uploaded: {', '.join(sorted(uploaded_fastq_files_names))}"
        )

    extra_fastq_files = uploaded_fastq_files_names - set(expected_fastq_files)
    if extra_fastq_files:
        extra_fastq_warning = (
            f"⚠️ Warning: Extra FASTQ file(s) were uploaded but ignored: {', '.join(sorted(extra_fastq_files))}."
        )
        logger.warning(extra_fastq_warning)

    logger.info(f"Sample '{sample_id}': All expected FASTQ files validated successfully.")

    antibiotics_file_name = (
        str(metadata_df.loc[0, "antibiotics file"]).strip()
        if "antibiotics file" in metadata_df.columns and not metadata_df["antibiotics file"].isna().iloc[0]
        else None
    )

    antibiotics_info = (
        str(metadata_df.loc[0, "antibiotics info"]).strip()
        if "antibiotics info" in metadata_df.columns and not metadata_df["antibiotics info"].isna().iloc[0]
        else None
    )

    if antibiotics_file_name and antibiotics_info:
        raise ValueError(
            f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously."
        )

    expected_antibiotics_file = antibiotics_file_name

    logger.debug(f"Expected Antibiotics File: {expected_antibiotics_file}")
    logger.debug(f"Uploaded Antibiotics File: {uploaded_antibiotics_file.name if uploaded_antibiotics_file else 'None'}")

    if expected_antibiotics_file and not uploaded_antibiotics_file:
        raise ValueError(f"Sample '{sample_id}': Expected antibiotics file '{expected_antibiotics_file}' is missing.")

    if expected_antibiotics_file and uploaded_antibiotics_file:
        if uploaded_antibiotics_file.name.strip() != expected_antibiotics_file.strip():
            raise ValueError(
                f"Sample '{sample_id}': Uploaded antibiotics file '{uploaded_antibiotics_file.name}' "
                f"does not match expected file '{expected_antibiotics_file}' in metadata."
            )

    antibiotics_df = pd.DataFrame()
    antibiotics_dfs_for_stats = []
    ab_warning = None

    if uploaded_antibiotics_file:
        valid_antibiotics, ab_warning, antibiotics_message, detected_delimiter_anti, antibiotics_df = validate_and_save_csv(
            uploaded_antibiotics_file,
            ANTIBIOTICS_COLUMNS
        )
        logger.debug(f"Detected delimiter (antibiotics): {detected_delimiter_anti}")

        if not valid_antibiotics:
            raise ValueError(f"FATAL: Sample '{sample_id}': Antibiotics file error: {antibiotics_message}")

        if antibiotics_df is None or antibiotics_df.empty:
            raise ValueError("Antibiotics file is empty or incorrectly formatted.")

        antibiotics_df.columns = antibiotics_df.columns.str.lower().str.strip()
        antibiotics_dfs_for_stats.append(antibiotics_df)

    submission = Submission(user=user)
    submission.submission_type = submission_type
    submission.resubmission_allowed = bool(metadata_warning)
    if metadata_warning:
        submission.metadata_warnings = metadata_message

    if ab_warning:
        submission.antibiotics_warnings = antibiotics_message

    if extra_fastq_files:
        submission.fastq_warning = extra_fastq_warning

    submission.submit_to_pipeline = bool(submit_to_pipeline)
    submission.metadata_statistics = generate_statistics(
        metadata_df,
        submission_type,
        antibiotics_dfs_for_stats,
    )

    submission.save()

    cleaned_metadata_file = generate_cleaned_file(metadata_file.name, metadata_df)
    UploadedFile.objects.create(
        submission=submission,
        file=metadata_file,
        cleaned_file=cleaned_metadata_file,
        file_type="metadata_raw",
        sample_id=sample_id
    )

    for expected_file in expected_fastq_files:
        matched_file = next((f for f in fastq_files if f.name == expected_file or f.name.startswith(expected_file)), None)
        if matched_file:
            UploadedFile.objects.create(
                submission=submission,
                file=matched_file,
                file_type="fastq",
                sample_id=sample_id
            )
            logger.debug(f"Saved FASTQ file: {matched_file.name}")

    if uploaded_antibiotics_file:
        cleaned_ab_file = generate_cleaned_file(uploaded_antibiotics_file.name, antibiotics_df)
        UploadedFile.objects.create(
            submission=submission,
            file=uploaded_antibiotics_file,
            cleaned_file=cleaned_ab_file,
            file_type="antibiotics_raw",
            sample_id=sample_id
        )

    message = "Single sample upload successful."
    if warning_message:
        message += f"\n{warning_message}"
    if extra_fastq_warning:
        message += f"\n{extra_fastq_warning}"

    upload_duration = time.time() - server_start

    try:
        recompute_global_statistics()
    except Exception as exc:
        logger.warning(f"Global statistics recompute failed after single upload: {exc}")

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": message,
        "upload_duration": upload_duration,
    }

@transaction.atomic
def handle_bulk_upload(*, user, metadata_file, antibiotics_files, fastq_files, submission_type, submit_to_pipeline=False):

    submission_type = normalize_submission_type(submission_type)

    if submission_type == "virus" and antibiotics_files:
        raise ValueError("Virus submissions do not accept antibiotics files.")

    server_start = time.time()

    if not metadata_file:
        raise ValueError("Metadata file is required but not provided.")

    if not fastq_files:
        raise ValueError("At least one sequencing file must be provided.")

    antibiotics_files = antibiotics_files or []

    logger.debug(f"Processing uploaded bulk metadata file: {metadata_file.name} (type: {type(metadata_file)})")

    if antibiotics_files:
        logger.debug(f"Processing {len(antibiotics_files)} uploaded antibiotics file(s).")
        for i, ab_file in enumerate(antibiotics_files):
            logger.debug(f"• Antibiotics file #{i+1}: {ab_file.name} (type: {type(ab_file)})")
    else:
        logger.debug("No antibiotics files uploaded.")

    logger.debug(f"Processing {len(fastq_files)} uploaded FASTQ file(s).")
    for i, f in enumerate(fastq_files):
        logger.debug(f"• FASTQ file #{i+1}: {f.name} (type: {type(f)})")

    metadata_warning_message = ""
    antibiotics_warning_message = ""
    extra_fastq_warning_message = ""

    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(
        metadata_file,
        METADATA_COLUMNS,
        ESSENTIAL_METADATA_COLUMNS
    )
    logger.debug(f"Detected delimiter (metadata): {detected_delimiter_meta}")

    if not valid_metadata:
        raise ValueError(f"Metadata file error: {metadata_message}")

    if metadata_warning:
        metadata_warning_message += f"{metadata_message}\n"
        logger.debug(f"Metadata file validated with warnings: {metadata_message}")
    else:
        logger.debug(f"Metadata file validated successfully: {metadata_file.name}")

    if metadata_df is None or metadata_df.empty:
        raise ValueError("Metadata file is empty or incorrectly formatted.")

    metadata_df.columns = metadata_df.columns.str.lower().str.strip()

    if "sample identifier" not in metadata_df.columns:
        raise ValueError("Metadata missing required column: 'sample identifier'.")

    metadata_df["sample identifier"] = metadata_df["sample identifier"].astype(str).str.strip()
    valid_bulk_sample_ids = metadata_df.loc[
        (metadata_df["sample identifier"] != "")
        & (metadata_df["sample identifier"].str.lower() != "nan"),
        "sample identifier",
    ]
    duplicate_sample_ids = valid_bulk_sample_ids[
        valid_bulk_sample_ids.str.lower().duplicated(keep=False)
    ].unique()
    if len(duplicate_sample_ids) > 0:
        duplicates = ", ".join(sorted(duplicate_sample_ids, key=str.lower))
        raise ValueError(
            f"Duplicate sample identifier(s) found in metadata file '{metadata_file.name}': {duplicates}. "
        )

    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
    uploaded_fastq_names = {f.name.strip() for f in fastq_files}
    logger.debug(f"Uploaded FASTQ filenames: {uploaded_fastq_names}")

    matched_fastq_files = set()

    def _safe_str(x):
        if x is None:
            return None
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return None
        return s

    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get("sample identifier")) or f"row {idx + 1}"
        if sample_id.startswith("row "):
            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

        illumina_r1 = _safe_str(row.get("illumina r1"))
        illumina_r2 = _safe_str(row.get("illumina r2"))
        nanopore = _safe_str(row.get("nanopore"))
        pacbio = _safe_str(row.get("pacbio"))

        expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]

        logger.debug(f"Sample '{sample_id}' expects FASTQ files: {expected_fastq_files}")

        if not any([illumina_r1, nanopore, pacbio]):
            raise ValueError(
                f"Sample '{sample_id}': Must include at least one platform file (Illumina R1, Nanopore, or PacBio)."
            ) 

        if illumina_r2 and not illumina_r1:
            raise ValueError(f"Sample '{sample_id}': Illumina R2 file provided without Illumina R1.")

        for fname in expected_fastq_files:
            if not any(fname.lower().endswith(ext) for ext in valid_extensions):
                raise ValueError(
                    f"Sample '{sample_id}': File '{fname}' has an invalid extension.\n"
                    f"Allowed extensions: {', '.join(valid_extensions)}"
                )
            matched_fastq_files.add(fname)

        missing = [f for f in expected_fastq_files if f not in uploaded_fastq_names]
        if missing:
            raise ValueError(
                f"Sample '{sample_id}': Some FASTQ files listed in metadata are missing from the upload.\n"
                f"Missing: {', '.join(sorted(missing))}\n"
                f"Expected: {', '.join(expected_fastq_files)}"
            )

        logger.info(f"Sample '{sample_id}': All expected FASTQ files validated successfully.")

    extra_fastq = uploaded_fastq_names - matched_fastq_files
    if extra_fastq:
        extra_fastq_warning_message += f"Extra FASTQ file(s) ignored: {', '.join(sorted(extra_fastq))}\n"
        logger.warning(extra_fastq_warning_message.strip())

    uploaded_antibiotics_by_name = {f.name.strip(): f for f in antibiotics_files}
    logger.debug(f"Uploaded antibiotics file names: {list(uploaded_antibiotics_by_name.keys())}")
    antibiotics_dfs_for_stats = []
    stats_seen_antibiotics_files = set()

    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get("sample identifier")) or f"row {idx + 1}"
        if sample_id.startswith("row "):
            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

        expected_ab_file = _safe_str(row.get("antibiotics file"))
        antibiotics_info = _safe_str(row.get("antibiotics info"))

        # inside handle_bulk_upload loop that processes antibiotics fields
        if submission_type == "virus":
            if expected_ab_file or antibiotics_info:
                raise ValueError(f"Sample '{sample_id}': Virus submissions must not include antibiotics fields.")
            continue

        if expected_ab_file and antibiotics_info:
            raise ValueError(
                f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously."
            )

        if expected_ab_file:
            uploaded_file = uploaded_antibiotics_by_name.get(expected_ab_file)
            if not uploaded_file:
                raise ValueError(f"Sample '{sample_id}': Missing expected antibiotics file '{expected_ab_file}'.")

            valid_ab, ab_warning, msg, delim, ab_df = validate_and_save_csv(uploaded_file, ANTIBIOTICS_COLUMNS)
            logger.debug(f"Detected delimiter (antibiotics): {delim}")

            if not valid_ab:
                raise ValueError(f"Sample '{sample_id}': Antibiotics file error: {msg}")

            if ab_warning:
                antibiotics_warning_message += f"Sample '{sample_id}': {msg}\n"

            if ab_df is not None and not ab_df.empty:
                ab_df.columns = ab_df.columns.str.lower().str.strip()
                if expected_ab_file not in stats_seen_antibiotics_files:
                    antibiotics_dfs_for_stats.append(ab_df)
                    stats_seen_antibiotics_files.add(expected_ab_file)

        elif antibiotics_info:
            logger.info(f"Sample '{sample_id}': Using antibiotics info from metadata.")
        else:
            logger.info(f"Sample '{sample_id}': No antibiotics file or info provided.")

    submission = Submission(user=user, is_bulk_upload=True)
    submission.submission_type = submission_type 
    submission.resubmission_allowed = bool(metadata_warning_message.strip())
    if metadata_warning_message.strip():
        submission.metadata_warnings = metadata_warning_message.strip()

    if antibiotics_warning_message.strip():
        submission.antibiotics_warnings = antibiotics_warning_message.strip()

    if extra_fastq_warning_message.strip():
        submission.fastq_warning = extra_fastq_warning_message.strip()

    submission.submit_to_pipeline = bool(submit_to_pipeline)
    submission.metadata_statistics = generate_statistics(
        metadata_df,
        submission_type,
        antibiotics_dfs_for_stats,
    )

    submission.save()

    cleaned_metadata_file = generate_cleaned_file(metadata_file.name, metadata_df)
    UploadedFile.objects.create(
        submission=submission,
        file=metadata_file,
        cleaned_file=cleaned_metadata_file,
        file_type="metadata_raw",
        sample_id="BULK" 
    )

    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get("sample identifier")) or f"row {idx + 1}"
        if sample_id.startswith("row "):
            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

        illumina_r1 = _safe_str(row.get("illumina r1"))
        illumina_r2 = _safe_str(row.get("illumina r2"))
        nanopore = _safe_str(row.get("nanopore"))
        pacbio = _safe_str(row.get("pacbio"))

        expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]

        for seq_filename in expected_fastq_files:
            matched_seq_file = next((f for f in fastq_files if f.name.strip() == seq_filename.strip()), None)
            if matched_seq_file:
                matched_seq_file.seek(0)
                UploadedFile.objects.create(
                    submission=submission,
                    file=matched_seq_file,
                    file_type="fastq",
                    sample_id=sample_id
                )
            else:
                logger.warning(f"Skipping missing sequencing file: {seq_filename} for sample '{sample_id}'")

        expected_ab_file = _safe_str(row.get("antibiotics file"))
        antibiotics_info = _safe_str(row.get("antibiotics info"))

        if expected_ab_file:
            uploaded_file = uploaded_antibiotics_by_name.get(expected_ab_file)
            if not uploaded_file:
                logger.warning(f"Skipping missing antibiotics file: {expected_ab_file} for sample '{sample_id}'")
                continue

            valid_ab, ab_warning, msg, delim, ab_df = validate_and_save_csv(uploaded_file, ANTIBIOTICS_COLUMNS)
            if not valid_ab:
                raise ValueError(f"Sample '{sample_id}': Antibiotics file error: {msg}")

            if ab_df is None or ab_df.empty:
                raise ValueError(f"Sample '{sample_id}': Antibiotics file is empty or incorrectly formatted.")

            ab_df.columns = ab_df.columns.str.lower().str.strip()

            cleaned_ab_file = generate_cleaned_file(uploaded_file.name, ab_df)

            uploaded_file.seek(0)
            if uploaded_file.closed:
                uploaded_file.open()

            UploadedFile.objects.create(
                submission=submission,
                file=uploaded_file,
                cleaned_file=cleaned_ab_file,
                file_type="antibiotics_raw",
                sample_id=sample_id
            )

        elif antibiotics_info:
            pass

    success_messages = ["Bulk upload completed successfully."]
    if metadata_warning_message.strip():
        success_messages.append("⚠️ Metadata file accepted with warnings.")
    if antibiotics_warning_message.strip():
        success_messages.append("⚠️ Some antibiotics files accepted with warnings.")
    if extra_fastq_warning_message.strip():
        success_messages.append("⚠️ Extra FASTQ files were ignored.")

    bulk_success_message = "\n".join(success_messages)

    upload_duration = time.time() - server_start

    try:
        recompute_global_statistics()
    except Exception as exc:
        logger.warning(f"Global statistics recompute failed after bulk upload: {exc}")

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": bulk_success_message,
        "upload_duration": upload_duration,
    }