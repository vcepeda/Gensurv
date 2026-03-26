import math
import os
from collections import Counter

import pandas as pd
from django.db import transaction

from gensurvapp.models import GlobalStatistics, Submission, UploadedFile


METADATA_FILE_TYPES = ("metadata_cleaned", "metadata_raw")


def _normalize_text(value):
    if value is None or pd.isna(value):
        return None
    value_str = str(value).strip()
    if not value_str or value_str.lower() == "nan":
        return None
    return value_str


def _read_uploaded_file_df(file_field):
    if not file_field:
        return None

    file_path = getattr(file_field, "path", None)
    file_name = getattr(file_field, "name", "") or ""

    if not file_path or not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_name.lower())[1]

    try:
        if ext == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path, sep=None, engine="python")
    except Exception:
        return None

    if df is None or df.empty:
        return None

    df.columns = df.columns.str.lower().str.strip()
    return df


def _get_submission_metadata_df(submission):
    metadata_files = submission.files.filter(file_type__in=METADATA_FILE_TYPES).order_by("id")

    cleaned_first = [f for f in metadata_files if f.cleaned_file]
    raw_next = [f for f in metadata_files if f.file]

    ordered_candidates = cleaned_first + raw_next

    for file_obj in ordered_candidates:
        candidate = file_obj.cleaned_file if file_obj.cleaned_file else file_obj.file
        df = _read_uploaded_file_df(candidate)
        if df is not None:
            return df

    return None


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _json_safe_numbers(values):
    safe_values = []
    for value in values:
        try:
            numeric = float(value)
            if math.isfinite(numeric):
                safe_values.append(numeric)
        except (TypeError, ValueError):
            continue
    return safe_values


@transaction.atomic
def recompute_global_statistics():
    submissions = list(Submission.objects.all().order_by("id"))

    platform_counts = {
        "illumina_r1_only": 0,
        "illumina_r1_r2": 0,
        "nanopore": 0,
        "pacbio": 0,
    }
    sir_counts = {
        "resistant": 0,
        "intermediate": 0,
        "susceptible": 0,
    }

    mic_values = []
    location_counter = Counter()
    global_sample_ids = set()
    global_isolate_species = set()

    total_metadata_rows = 0

    for submission in submissions:
        stats = submission.metadata_statistics or {}

        total_metadata_rows += _safe_int(stats.get("total_rows", 0))
        platform_counts["illumina_r1_only"] += _safe_int(stats.get("illumina_r1_only_count", 0))
        platform_counts["illumina_r1_r2"] += _safe_int(stats.get("illumina_r1_r2_count", 0))
        platform_counts["nanopore"] += _safe_int(stats.get("nanopore_count", 0))
        platform_counts["pacbio"] += _safe_int(stats.get("pacbio_count", 0))

        antibiotics_stats = stats.get("antibiotics", {}) if isinstance(stats, dict) else {}
        sir_stats = antibiotics_stats.get("sir_counts", {}) if isinstance(antibiotics_stats, dict) else {}

        sir_counts["resistant"] += _safe_int(sir_stats.get("resistant", 0))
        sir_counts["intermediate"] += _safe_int(sir_stats.get("intermediate", 0))
        sir_counts["susceptible"] += _safe_int(sir_stats.get("susceptible", 0))

        mic_values.extend(_json_safe_numbers(antibiotics_stats.get("mic_numeric_values", [])))

        metadata_df = _get_submission_metadata_df(submission)
        if metadata_df is None:
            continue

        if "sample identifier" in metadata_df.columns:
            sample_series = metadata_df["sample identifier"].map(_normalize_text)
            global_sample_ids.update([value.lower() for value in sample_series if value])

        if "isolate species" in metadata_df.columns:
            species_series = metadata_df["isolate species"].map(_normalize_text)
            global_isolate_species.update([value.lower() for value in species_series if value])

        city_series = metadata_df["city"].map(_normalize_text) if "city" in metadata_df.columns else pd.Series([None] * len(metadata_df))
        postal_series = metadata_df["postal code"].map(_normalize_text) if "postal code" in metadata_df.columns else pd.Series([None] * len(metadata_df))
        state_series = metadata_df["state"].map(_normalize_text) if "state" in metadata_df.columns else pd.Series([None] * len(metadata_df))
        country_series = metadata_df["country"].map(_normalize_text) if "country" in metadata_df.columns else pd.Series([None] * len(metadata_df))

        for city, postal_code, state, country in zip(city_series, postal_series, state_series, country_series):
            if not any([city, postal_code, state, country]):
                continue
            key = (
                city or "",
                postal_code or "",
                state or "",
                country or "",
            )
            location_counter[key] += 1

    map_location_counts = [
        {
            "city": city,
            "postal_code": postal_code,
            "state": state,
            "country": country,
            "count": count,
        }
        for (city, postal_code, state, country), count in sorted(
            location_counter.items(),
            key=lambda item: (-item[1], item[0][3], item[0][2], item[0][0]),
        )
    ]

    global_stats, _ = GlobalStatistics.objects.get_or_create(singleton_key=1)
    global_stats.stats_version = 1
    global_stats.total_submissions = len(submissions)
    global_stats.total_metadata_rows = total_metadata_rows
    global_stats.total_fastq_files = UploadedFile.objects.filter(file_type="fastq").count()
    global_stats.total_antibiotics_files = UploadedFile.objects.filter(file_type="antibiotics_raw").count()
    global_stats.total_unique_sample_identifiers = len(global_sample_ids)
    global_stats.total_unique_isolate_species = len(global_isolate_species)
    global_stats.platform_counts = platform_counts
    global_stats.sir_counts = sir_counts
    global_stats.mic_numeric_values = mic_values
    global_stats.map_location_counts = map_location_counts
    global_stats.save()

    return global_stats
