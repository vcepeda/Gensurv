"""Conversion helpers for user-facing Norovirus V2 metadata."""

import hashlib
from datetime import datetime

import pandas as pd

from gensurvapp.num_sar_constants import NUM_SAR_METADATA_COLUMNS
from gensurvapp.norovirus_v2_constants import NOROVIRUS_MELDETATBESTAND


# Source names are lower-case because validate_and_save_csv normalizes headers.
DIRECT_COLUMN_MAP = {
    "LAB_SEQUENCE_ID": "lab_sequence_id",
    "SPECIES": "species",
    "ISOLATE": "isolate",
    "Subtype": "subtype",
    "Typing strategy": "typing_strategy",
    "DATE_OF_SAMPLING": "date_of_sampling",
    "ISOLATION SOURCE": "isolation_source",
    "Storage duration": "storage duration",
    "County": "county",
    "Country": "country",
    "DATE_OF_RECEIVING": "date_of_receiving",
    "PRIME_DIAGNOSTIC_LAB.CITY": "prime_diagnostic_lab.city",
    "PRIME_DIAGNOSTIC_LAB.POSTAL_CODE": "prime_diagnostic_lab.postal_code",
    "PRIME_DIAGNOSTIC_LAB.COUNTRY": "prime_diagnostic_lab.country",
    "PRIME_DIAGNOSTIC_LAB.FEDERAL_STATE": "prime_diagnostic_lab.federal_state",
    "HOST_SEX": "host_sex",
    "Age Group": "age group",
    "HOST_BIRTH_MONTH": "host_birth_month",
    "HOST_BIRTH_YEAR": "host_birth_year",
    "Patient status": "patient status",
    "Non patient sample": "non patient sample",
    "suspected outbreak": "suspected outbreak",
    "SEQUENCING_REASON": "sequencing_reason",
    "DATE_OF_SEQUENCING": "date_of_sequencing",
    "SEQUENCING_LAB.NAME": "sequencing_lab.name",
    "SEQUENCING_LAB.EMAIL": "sequencing_lab.email",
    "SEQUENCING_LAB.ADDRESS": "sequencing_lab.address",
    "SEQUENCING_LAB.CITY": "sequencing_lab.city",
    "SEQUENCING_LAB.POSTAL_CODE": "sequencing_lab.postal_code",
    "SEQUENCING_LAB.COUNTRY": "sequencing_lab.country",
    "REPOSITORY_NAME": "repository_name",
    "SEQUENCING_PLATFORM": "sequencing_platform",
    "SEQUENCING_INSTRUMENT": "sequencing_instrument",
    "Library Preparation Kit": "library preparation kit",
    "NAME_AMP_PROTOCOL": "name_amp_protocol",
}


def _safe_str(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def map_sequencing_files_to_num_sar(row):
    """Map one normalized V2 row to NUM-SAR FILE_1/FILE_2 fields.

    The uploaded files themselves are not renamed. Only their references in
    the generated NUM-SAR metadata are mapped.
    """
    illumina_r1 = _safe_str(row.get("illumina r1"))
    illumina_r2 = _safe_str(row.get("illumina r2"))
    nanopore = _safe_str(row.get("nanopore"))
    pacbio = _safe_str(row.get("pacbio"))

    if illumina_r2 and not illumina_r1:
        raise ValueError("Illumina R2 cannot be provided without Illumina R1.")

    platform_families = [
        name
        for name, is_present in (
            ("Illumina", bool(illumina_r1 or illumina_r2)),
            ("Nanopore", bool(nanopore)),
            ("PacBio", bool(pacbio)),
        )
        if is_present
    ]

    if not platform_families:
        raise ValueError(
            "At least one of Illumina R1, Nanopore, or PacBio must be provided."
        )
    if len(platform_families) > 1:
        raise ValueError(
            "A single NUM-SAR row cannot contain multiple sequencing platform "
            f"families: {', '.join(platform_families)}."
        )

    if illumina_r1:
        file_1_name = illumina_r1
        file_2_name = illumina_r2
    elif nanopore:
        file_1_name = nanopore
        file_2_name = None
    else:
        file_1_name = pacbio
        file_2_name = None

    return {
        "FILE_1_NAME": file_1_name,
        "FILE_2_NAME": file_2_name,
    }


def add_num_sar_file_columns(metadata_df):
    """Return a copy of a normalized V2 DataFrame with NUM-SAR file columns."""
    converted_df = metadata_df.copy()
    mapped_rows = [
        map_sequencing_files_to_num_sar(row)
        for _, row in converted_df.iterrows()
    ]
    converted_df["FILE_1_NAME"] = [row["FILE_1_NAME"] for row in mapped_rows]
    converted_df["FILE_2_NAME"] = [row["FILE_2_NAME"] for row in mapped_rows]
    return converted_df


def _normalize_sampling_date(value):
    text = _safe_str(value)
    if text is None:
        return None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(
        f"Invalid DATE_OF_SAMPLING '{text}'. Expected YYYY-MM-DD or DD/MM/YYYY."
    )


def calculate_sha256(uploaded_file):
    """Calculate an uploaded file's SHA-256 and restore its stream position."""
    original_position = None
    try:
        original_position = uploaded_file.tell()
    except (AttributeError, OSError):
        pass

    uploaded_file.seek(0)
    digest = hashlib.sha256()
    if hasattr(uploaded_file, "chunks"):
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
    else:
        while True:
            chunk = uploaded_file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    uploaded_file.seek(original_position if original_position is not None else 0)
    return digest.hexdigest()


def build_num_sar_metadata(metadata_df, uploaded_files):
    """Build the currently derivable portion of the old NUM-SAR metadata.

    Fields that require an agreed default or external mapping remain empty.
    """
    uploaded_by_name = {uploaded.name.strip(): uploaded for uploaded in uploaded_files}
    output_rows = []

    for _, source_row in metadata_df.iterrows():
        output_row = {column: None for column in NUM_SAR_METADATA_COLUMNS}
        output_row["MELDETATBESTAND"] = NOROVIRUS_MELDETATBESTAND

        for target_column, source_column in DIRECT_COLUMN_MAP.items():
            output_row[target_column] = _safe_str(source_row.get(source_column))

        output_row["DATE_OF_SAMPLING"] = _normalize_sampling_date(
            source_row.get("date_of_sampling")
        )

        file_mapping = map_sequencing_files_to_num_sar(source_row)
        output_row.update(file_mapping)

        file_1 = uploaded_by_name.get(file_mapping["FILE_1_NAME"])
        if file_1 is None:
            raise ValueError(
                f"Cannot calculate FILE_1_SHA256SUM: uploaded file "
                f"'{file_mapping['FILE_1_NAME']}' was not found."
            )
        output_row["FILE_1_SHA256SUM"] = calculate_sha256(file_1)

        if file_mapping["FILE_2_NAME"]:
            file_2 = uploaded_by_name.get(file_mapping["FILE_2_NAME"])
            if file_2 is None:
                raise ValueError(
                    f"Cannot calculate FILE_2_SHA256SUM: uploaded file "
                    f"'{file_mapping['FILE_2_NAME']}' was not found."
                )
            output_row["FILE_2_SHA256SUM"] = calculate_sha256(file_2)

        output_rows.append(output_row)

    return pd.DataFrame(output_rows, columns=NUM_SAR_METADATA_COLUMNS.keys())
