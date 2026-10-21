"""Field-level validation for user-facing Norovirus V2 metadata."""

import re
from urllib.parse import urlparse

import pandas as pd


VALID_HOST_SEX = {"male", "female", "diverse", "unknown"}
VALID_AGE_GROUPS = {"0-4", "5-14", "15-34", "35-59", "60-79", "80+", "unknown"}
VALID_PATIENT_STATUSES = {"outpatient", "inpatient", "unknown"}
VALID_SUSPECTED_OUTBREAK = {"yes", "no"}
VALID_STORAGE_DURATIONS = {
    "< 1 week",
    "1 week - 1 month",
    "1-6 months",
    "6-12 months",
    "> 12 months",
}

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _safe_str(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _normalize_dash_text(value):
    return re.sub(r"\s+", " ", value.replace("–", "-").replace("—", "-")).strip()


def _is_valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def validate_norovirus_v2_fields(metadata_df):
    """Raise ValueError containing all V2 field-validation errors."""
    errors = []

    for idx, row in metadata_df.iterrows():
        row_number = idx + 1

        for column, label in (
            ("prime_diagnostic_lab.email", "PRIME_DIAGNOSTIC_LAB.EMAIL"),
            ("sequencing_lab.email", "SEQUENCING_LAB.EMAIL"),
        ):
            value = _safe_str(row.get(column))
            if value and not EMAIL_PATTERN.fullmatch(value):
                errors.append(f"Row {row_number}, {label}: invalid email address '{value}'.")

        geographic_location = _safe_str(row.get("geographic_location"))
        if geographic_location and not re.fullmatch(r"\d{3}", geographic_location):
            errors.append(
                f"Row {row_number}, GEOGRAPHIC_LOCATION: expected exactly three digits."
            )

        repository_link = _safe_str(row.get("repository_link"))
        if repository_link and not _is_valid_url(repository_link):
            errors.append(
                f"Row {row_number}, REPOSITORY_LINK: expected a valid HTTP or HTTPS URL."
            )

        host_sex = _safe_str(row.get("host_sex"))
        if host_sex and host_sex.lower() not in VALID_HOST_SEX:
            errors.append(
                f"Row {row_number}, HOST_SEX: expected Male, Female, Diverse, or Unknown."
            )

        age_group = _safe_str(row.get("age group"))
        if age_group:
            normalized_age_group = _normalize_dash_text(age_group).lower()
            if normalized_age_group not in VALID_AGE_GROUPS:
                errors.append(
                    f"Row {row_number}, Age Group: expected 0-4, 5-14, 15-34, "
                    "35-59, 60-79, 80+, or Unknown."
                )

        patient_status = _safe_str(row.get("patient status"))
        if patient_status and patient_status.lower() not in VALID_PATIENT_STATUSES:
            errors.append(
                f"Row {row_number}, Patient Status: expected Outpatient, Inpatient, or Unknown."
            )

        suspected_outbreak = _safe_str(row.get("suspected outbreak"))
        if suspected_outbreak and suspected_outbreak.lower() not in VALID_SUSPECTED_OUTBREAK:
            errors.append(
                f"Row {row_number}, Suspected outbreak: expected Yes or No."
            )

        storage_duration = _safe_str(row.get("storage duration"))
        if storage_duration:
            normalized_duration = _normalize_dash_text(storage_duration).lower()
            normalized_choices = {choice.lower() for choice in VALID_STORAGE_DURATIONS}
            if normalized_duration not in normalized_choices:
                errors.append(
                    f"Row {row_number}, Storage Duration: invalid value '{storage_duration}'."
                )

        birth_month = _safe_str(row.get("host_birth_month"))
        if birth_month:
            if not birth_month.isdigit() or not 1 <= int(birth_month) <= 12:
                errors.append(
                    f"Row {row_number}, HOST_BIRTH_MONTH: expected a number from 1 to 12."
                )

        birth_year = _safe_str(row.get("host_birth_year"))
        if birth_year and not re.fullmatch(r"\d{4}", birth_year):
            errors.append(
                f"Row {row_number}, HOST_BIRTH_YEAR: expected a four-digit year."
            )

        # ISOLATION_SOURCE, SEQUENCING_REASON, SEQUENCING_PLATFORM, and
        # SEQUENCING_INSTRUMENT intentionally accept any non-empty custom text.
        # Values outside the PDF's enumerated choices represent its Other category.

    if errors:
        raise ValueError("\n".join(errors))
