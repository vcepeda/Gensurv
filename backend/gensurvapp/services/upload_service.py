import time
import pandas as pd
from django.db import transaction

# ✅ IMPORTANT: adjust these imports to match your project paths
from gensurvapp.models import Submission, UploadedFile
from gensurvapp.utils import validate_and_save_csv, generate_cleaned_file
from gensurvapp.constants import METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS, ANTIBIOTICS_COLUMNS

import logging
logger = logging.getLogger(__name__)


@transaction.atomic
def handle_single_upload(*, user, metadata_file, uploaded_antibiotics_file, fastq_files, submit_to_pipeline=False):

    server_start = time.time()

    warning_message = None
    extra_fastq_warning = ""
    antibiotics_message = None

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

    # sample id
    if "sample identifier" not in metadata_df.columns:
        raise ValueError("Metadata missing required column: 'sample identifier'.")

    sample_id = str(metadata_df.loc[0, "sample identifier"]).strip()
    if not sample_id or sample_id.lower() == "nan":
        raise ValueError("Metadata has missing/invalid 'sample identifier' in first row.")

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

    submission = Submission(user=user)
    submission.resubmission_allowed = bool(metadata_warning)
    if metadata_warning:
        submission.metadata_warnings = metadata_message

    if ab_warning:
        submission.antibiotics_warnings = antibiotics_message

    if extra_fastq_files:
        submission.fastq_warning = extra_fastq_warning

    submission.submit_to_pipeline = bool(submit_to_pipeline)

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

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": message,
        "upload_duration": upload_duration,
    }

@transaction.atomic
def handle_bulk_upload(*, user, metadata_file, antibiotics_files, fastq_files, submit_to_pipeline=False):

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

    for idx, row in metadata_df.iterrows():
        sample_id = _safe_str(row.get("sample identifier")) or f"row {idx + 1}"
        if sample_id.startswith("row "):
            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

        expected_ab_file = _safe_str(row.get("antibiotics file"))
        antibiotics_info = _safe_str(row.get("antibiotics info"))

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

        elif antibiotics_info:
            logger.info(f"Sample '{sample_id}': Using antibiotics info from metadata.")
        else:
            logger.info(f"Sample '{sample_id}': No antibiotics file or info provided.")

    submission = Submission(user=user, is_bulk_upload=True)
    submission.resubmission_allowed = bool(metadata_warning_message.strip())
    if metadata_warning_message.strip():
        submission.metadata_warnings = metadata_warning_message.strip()

    if antibiotics_warning_message.strip():
        submission.antibiotics_warnings = antibiotics_warning_message.strip()

    if extra_fastq_warning_message.strip():
        submission.fastq_warning = extra_fastq_warning_message.strip()

    submission.submit_to_pipeline = bool(submit_to_pipeline)

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

    return {
        "submission_id": submission.id,
        "resubmission_allowed": submission.resubmission_allowed,
        "message": bulk_success_message,
        "upload_duration": upload_duration,
    }