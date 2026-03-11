from collections import defaultdict
from django.db.models import Prefetch, Count
from gensurvapp.models import Submission, UploadedFile, FileHistory, AnalysisResult
from gensurvapp.utils import (
    cached_parse_metadata_sample_ids,
    cached_parse_metadata_antibiotics_info,
    parse_metadata_antibiotics_info,
)
from gensurvapp.utils import admin_only_upload_test  # wherever your function lives

def build_dashboard_rows_for_user(user):
    sample_files_qs = UploadedFile.objects.filter(file_type__in=["metadata_cleaned", "metadata_raw", "metadata"])
    antibiotics_files_qs = UploadedFile.objects.filter(file_type__in=["antibiotics", "antibiotics_raw", "antibiotics_cleaned"])
    fastq_files_qs = UploadedFile.objects.filter(file_type="fastq")

    base_qs = Submission.objects.select_related("user").prefetch_related(
        Prefetch("files", queryset=sample_files_qs, to_attr="prefetched_sample_files"),
        Prefetch("files", queryset=antibiotics_files_qs, to_attr="prefetched_antibiotics_files"),
        Prefetch("files", queryset=fastq_files_qs, to_attr="prefetched_fastq_files"),
    )

    if admin_only_upload_test(user):
        submissions = base_qs.order_by("-created_at")
    else:
        submissions = base_qs.filter(user=user).order_by("-created_at")

    history_counts = FileHistory.objects.values("submission_id", "file_type").annotate(count=Count("id"))
    history_lookup = {(e["submission_id"], e["file_type"]): e["count"] for e in history_counts}

    # collect sample ids for analysis lookup
    all_sample_ids = set()
    for s in submissions:
        for fq in s.prefetched_fastq_files:
            if fq.sample_id:
                all_sample_ids.add(fq.sample_id)

    analysis_lookup = {}
    if all_sample_ids:
        analysis_results = (
            AnalysisResult.objects
            .filter(sample_id__in=all_sample_ids)
            .order_by("-completion_date")
        )

        for r in analysis_results:
            sid = r.sample_id
            if sid not in analysis_lookup:
                analysis_lookup[sid] = r.status

    rows = []
    for submission in submissions:
        antibiotics_files = list(submission.prefetched_antibiotics_files)
        fastq_files = list(submission.prefetched_fastq_files)

        # metadata: prefer cleaned else raw
        cleaned_metadata = submission.files.filter(file_type="metadata_cleaned").first()
        if not cleaned_metadata:
            cleaned_metadata = submission.files.filter(file_type="metadata_raw").first()
        raw_metadata = submission.files.filter(file_type="metadata_raw").first()

        grouped_fastq_files = defaultdict(list)
        sample_analysis_status = {}

        for fq in fastq_files:
            sid = fq.sample_id or "unknown"
            grouped_fastq_files[sid].append(fq)
            if sid != "unknown":
                sample_analysis_status[sid] = analysis_lookup.get(sid, "pending")

        antibiotics_info = {}
        # single upload
        if not submission.is_bulk_upload:
            sample_id = None
            if cleaned_metadata and cleaned_metadata.file:
                try:
                    sample_id = cached_parse_metadata_sample_ids(cleaned_metadata.file.path)
                except Exception:
                    sample_id = None

            if not antibiotics_files and cleaned_metadata and cleaned_metadata.file and sample_id:
                try:
                    info = parse_metadata_antibiotics_info(cleaned_metadata.file.path, target_sample_id=sample_id)
                    if info:
                        antibiotics_info = {sample_id: info}
                except Exception:
                    antibiotics_info = {}
        else:
            # bulk upload
            if cleaned_metadata and cleaned_metadata.file:
                try:
                    full_info = cached_parse_metadata_antibiotics_info(cleaned_metadata.file.path) or {}
                except Exception:
                    full_info = {}
                sample_ids_with_file = {f.sample_id for f in antibiotics_files if f.file}
                antibiotics_info = {sid: info for sid, info in full_info.items() if sid not in sample_ids_with_file}

        metadata_resub_count = history_lookup.get((submission.id, "metadata_raw"), 0)
        antibiotics_resub_count = history_lookup.get((submission.id, "antibiotics_raw"), 0)

        rows.append({
            "submission": submission,
            "raw_metadata": raw_metadata,
            "cleaned_metadata": cleaned_metadata,
            "antibiotics_files": antibiotics_files,
            "antibiotics_info": antibiotics_info,
            "grouped_fastq_files": dict(grouped_fastq_files),
            "sample_analysis_status": sample_analysis_status,
            "metadata_resub_count": metadata_resub_count,
            "antibiotics_resub_count": antibiotics_resub_count,
        })

    return rows