# gensurvapp/views_api.py
from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import time
import logging
import csv

from .services.upload_service import handle_single_upload, handle_bulk_upload, normalize_submission_type
from .services.upload_service_num_sar import (
    handle_single_upload as handle_num_sar_single_upload,
    handle_bulk_upload as handle_num_sar_bulk_upload,
)
from .services.upload_service_cogdat import handle_cogdat_upload
from .num_sar_constants import NUM_SAR_SUBMISSION_TYPES

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from pathlib import Path
import mimetypes

from gensurvapp.models import *
from gensurvapp.services.dashboard_service import build_dashboard_rows_for_user
from gensurvapp.services.global_stats_service import recompute_global_statistics, _get_submission_metadata_df, _normalize_text
from gensurvapp.services.bactopia_report_service import load_bactopia_report
from gensurvapp.scripts.serializers import (
    SubmissionDashboardRowSerializer,
    SubmissionSampleListSerializer,
    SingleUploadSerializer,
    BulkUploadSerializer,
    CogdatUploadSerializer,
    AdminToggleAnalysisStatusSerializer,
)
from gensurvapp.utils import admin_only_upload_test, archive_file_to_submission_history

from gensurvapp.utils import (
    validate_and_save_csv,
    generate_cleaned_file,
    compare_metadata_with_uploaded_files,
    METADATA_COLUMNS,
    ESSENTIAL_METADATA_COLUMNS,
)
import os

logger = logging.getLogger(__name__)


class SingleUploadAPIView(APIView):
    """
    API endpoint for single sample upload.
    
    POST /api/upload/single/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SingleUploadSerializer(data=request.data)
        submission_type = request.query_params.get("type", "gensurv")
        dry_run = request.query_params.get("dry_run", "").strip().lower() in ("1", "true", "yes")

        try:
            submission_type = normalize_submission_type(submission_type)
        except ValueError as ve:
            return Response(
                {"success": False, "error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract validated data
            metadata_file = serializer.validated_data['metadata_file']
            antibiotics_file = serializer.validated_data.get('antibiotics_file')
            fastq_files = serializer.validated_data['fastq_files']
            submit_to_pipeline = serializer.validated_data.get('submit_to_pipeline', False)
            upload_start_time = serializer.validated_data.get('upload_start_time')

            if submission_type in NUM_SAR_SUBMISSION_TYPES:
                result = handle_num_sar_single_upload(
                    user=request.user,
                    metadata_file=metadata_file,
                    fastq_files=fastq_files,
                    submit_to_pipeline=submit_to_pipeline,
                    submission_type=submission_type,
                    dry_run=dry_run,
                )
            else:
                result = handle_single_upload(
                    user=request.user,
                    metadata_file=metadata_file,
                    uploaded_antibiotics_file=antibiotics_file,
                    fastq_files=fastq_files,
                    submit_to_pipeline=submit_to_pipeline,
                    submission_type=submission_type,
                    dry_run=dry_run,
                )

            response_data = {
                "success": True,
                "submission_id": result["submission_id"],
                "resubmission_allowed": result["resubmission_allowed"],
                "message": result["message"],
                "upload_duration": result["upload_duration"],
                "dry_run": result.get("dry_run", False),
            }

            if upload_start_time:
                now = time.time()
                client_total = now - upload_start_time
                network_delay = client_total - result["upload_duration"]
                response_data.update({
                    "client_total_upload_time": client_total,
                    "network_delay": network_delay
                })

            return Response(response_data, status=status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED)

        except ValueError as ve:
            # Validation errors from business logic
            logger.warning(f"Single upload validation error: {str(ve)}")
            return Response(
                {
                    "success": False,
                    "error": str(ve),
                    "error_type": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Unexpected errors
            logger.error(f"Single upload error: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"An unexpected error occurred: {str(e)}",
                    "error_type": "server_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkUploadAPIView(APIView):
    """
    API endpoint for bulk sample upload.
    
    POST /api/upload/bulk/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = BulkUploadSerializer(data=request.data)
        submission_type = request.query_params.get("type", "gensurv")
        dry_run = request.query_params.get("dry_run", "").strip().lower() in ("1", "true", "yes")

        try:
            submission_type = normalize_submission_type(submission_type)
        except ValueError as ve:
            return Response(
                {"success": False, "error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract validated data
            metadata_file = serializer.validated_data['metadata_file']
            antibiotics_files = serializer.validated_data.get('antibiotics_files', [])
            fastq_files = serializer.validated_data['fastq_files']
            submit_to_pipeline = serializer.validated_data.get('submit_to_pipeline', False)
            upload_start_time = serializer.validated_data.get('upload_start_time')

            # Call the business logic handler
            if submission_type in NUM_SAR_SUBMISSION_TYPES:
                result = handle_num_sar_bulk_upload(
                    user=request.user,
                    metadata_file=metadata_file,
                    fastq_files=fastq_files,
                    submit_to_pipeline=submit_to_pipeline,
                    submission_type=submission_type,
                    dry_run=dry_run,
                )
            else:
                result = handle_bulk_upload(
                    user=request.user,
                    metadata_file=metadata_file,
                    antibiotics_files=antibiotics_files,
                    fastq_files=fastq_files,
                    submit_to_pipeline=submit_to_pipeline,
                    submission_type=submission_type,
                    dry_run=dry_run,
                )

            # Calculate timing metrics if client sent start time
            response_data = {
                "success": True,
                "submission_id": result["submission_id"],
                "resubmission_allowed": result["resubmission_allowed"],
                "message": result["message"],
                "upload_duration": result["upload_duration"],
                "dry_run": result.get("dry_run", False),
            }

            if upload_start_time:
                now = time.time()
                client_total = now - upload_start_time
                network_delay = client_total - result["upload_duration"]
                response_data.update({
                    "client_total_upload_time": client_total,
                    "network_delay": network_delay
                })

            return Response(response_data, status=status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED)

        except ValueError as ve:
            # Validation errors from business logic
            logger.warning(f"Bulk upload validation error: {str(ve)}")
            return Response(
                {
                    "success": False,
                    "error": str(ve),
                    "error_type": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Unexpected errors
            logger.error(f"Bulk upload error: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"An unexpected error occurred: {str(e)}",
                    "error_type": "server_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CogdatUploadAPIView(APIView):
    """
    API endpoint for COGDAT fastq-only uploads (no metadata file; sample IDs
    are derived from filenames and checked against the COGDAT sample roster).

    POST /api/upload/cogdat/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CogdatUploadSerializer(data=request.data)
        dry_run = request.query_params.get("dry_run", "").strip().lower() in ("1", "true", "yes")

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fastq_files = serializer.validated_data['fastq_files']
            upload_start_time = serializer.validated_data.get('upload_start_time')

            result = handle_cogdat_upload(
                user=request.user,
                fastq_files=fastq_files,
                dry_run=dry_run,
            )

            response_data = {
                "success": True,
                "submission_id": result["submission_id"],
                "resubmission_allowed": result["resubmission_allowed"],
                "message": result["message"],
                "upload_duration": result["upload_duration"],
                "dry_run": result.get("dry_run", False),
            }

            if upload_start_time:
                now = time.time()
                client_total = now - upload_start_time
                network_delay = client_total - result["upload_duration"]
                response_data.update({
                    "client_total_upload_time": client_total,
                    "network_delay": network_delay
                })

            return Response(response_data, status=status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED)

        except ValueError as ve:
            logger.warning(f"COGDAT upload validation error: {str(ve)}")
            return Response(
                {
                    "success": False,
                    "error": str(ve),
                    "error_type": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"COGDAT upload error: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"An unexpected error occurred: {str(e)}",
                    "error_type": "server_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope = (request.query_params.get("scope") or "all").strip().lower()
        if scope not in {"mine", "others", "all"}:
            scope = "all"

        rows = build_dashboard_rows_for_user(request.user, scope=scope)

        payload = []
        for r in rows:
            s = r["submission"]
            raw = r["raw_metadata"]
            cleaned = r["cleaned_metadata"]

            def file_obj(upl):
                if not upl:
                    return None
                out = {}
                if upl.file:
                    out["raw_url"] = request.build_absolute_uri(upl.file.url)
                    out["raw_name"] = os.path.basename(upl.file.name)
                if upl.cleaned_file:
                    out["cleaned_url"] = request.build_absolute_uri(upl.cleaned_file.url)
                    out["cleaned_name"] = os.path.basename(upl.cleaned_file.name)
                return out or None

            antibiotics_files_payload = []
            for f in r["antibiotics_files"]:
                if not f.file:
                    continue
                antibiotics_files_payload.append({
                    "sample_id": f.sample_id or "Unnamed Sample",
                    "raw_url": request.build_absolute_uri(f.file.url),
                    "raw_name": os.path.basename(f.file.name),
                    "cleaned_url": request.build_absolute_uri(f.cleaned_file.url) if f.cleaned_file else None,
                    "cleaned_name": os.path.basename(f.cleaned_file.name) if f.cleaned_file else None,
                })

            grouped_fastq_payload = {}
            for sid, files in r["grouped_fastq_files"].items():
                grouped_fastq_payload[sid] = [
                    {
                        "url": request.build_absolute_uri(f.file.url) if f.file else None,
                        "name": os.path.basename(f.file.name) if f.file else None,
                    }
                    for f in files
                    if f.file
                ]

            payload.append({
                "username": s.user.username,
                "institution": getattr(s.user, "institution", "") or "",
                "submission_id": s.id,
                "created_at": s.created_at,
                "submission_type": s.submission_type,
                "is_own": s.user_id == request.user.id,

                "metadata": {
                    "files": file_obj(cleaned) or file_obj(raw),
                    "warnings": s.metadata_warnings or "",
                    "resub_count": r["metadata_resub_count"],
                    "can_resubmit": bool(s.resubmission_allowed),
                },
                "antibiotics": {
                    "files": antibiotics_files_payload,
                    "info": r["antibiotics_info"],
                    "warnings": s.antibiotics_warnings or "",
                },
                "fastq": {
                    "grouped": grouped_fastq_payload,
                    "extra_warning": s.extra_fastq_warning if hasattr(s, "extra_fastq_warning") else "",
                },
                "analysis": {
                    "statuses": r["sample_analysis_status"],
                },
                "qc": r["qc_summary"],
                "deletion": {
                    "requested": bool(s.deletion_requested),
                }
            })

        # validate shape (optional)
        ser = SubmissionDashboardRowSerializer(data=payload, many=True)
        ser.is_valid(raise_exception=True)
        return Response(ser.data)


class AdminToggleAnalysisStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not admin_only_upload_test(request.user):
            return Response({"detail": "Forbidden"}, status=403)

        serializer = AdminToggleAnalysisStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission_id = serializer.validated_data["submission_id"]
        sample_id = serializer.validated_data["sample_id"].strip()

        if not sample_id:
            return Response({"detail": "sample_id is required."}, status=400)

        submission = get_object_or_404(Submission, id=submission_id)

        analysis_result = (
            AnalysisResult.objects
            .filter(submission=submission, sample_id=sample_id)
            .order_by("-completion_date", "-id")
            .first()
        )

        current_status = (analysis_result.status if analysis_result else "pending").strip().lower()
        is_finished_like = current_status in {"finished", "completed", "done"}
        new_status = "pending" if is_finished_like else "finished"

        defaults = {"status": new_status}
        if new_status == "finished":
            defaults["completion_date"] = timezone.now()

        updated_result, _ = AnalysisResult.objects.update_or_create(
            submission=submission,
            sample_id=sample_id,
            defaults=defaults,
        )

        return Response(
            {
                "ok": True,
                "submission_id": submission.id,
                "sample_id": sample_id,
                "status": updated_result.status,
            },
            status=200,
        )


class RequestSubmissionDeletionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)

        # enforce owner unless admin
        if not admin_only_upload_test(request.user) and submission.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

        if submission.deletion_requested:
            return Response({"ok": True, "message": "Deletion already requested."})

        admin_email = settings.ADMINS[0][1] if settings.ADMINS else settings.DEFAULT_FROM_EMAIL
        send_mail(
            subject=f"🚨 Deletion Request: Submission #{submission.id}",
            message=(
                f"User {request.user.email} has requested deletion of submission #{submission.id}.\n\n"
                f"Submission created at: {submission.created_at}\n"
                f"Bulk upload: {submission.is_bulk_upload}\n"
                f"Submission ID: {submission.id}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
        )
        submission.deletion_requested = True
        submission.save(update_fields=["deletion_requested"])
        return Response({"ok": True, "message": "Deletion request sent."})


class ResubmissionHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id, file_type):
        submission = get_object_or_404(Submission, id=submission_id)

        if not admin_only_upload_test(request.user) and submission.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

        history = (
            FileHistory.objects
            .filter(submission=submission, file_type=f"{file_type}_raw")
            .order_by("-timestamp")
        )

        out = []
        for h in history:
            out.append({
                "timestamp": h.timestamp,
                "raw_url": request.build_absolute_uri(h.old_file.url) if h.old_file else None,
                "cleaned_url": request.build_absolute_uri(h.cleaned_file.url) if h.cleaned_file else None,
            })
        return Response({"submission_id": submission.id, "file_type": file_type, "history": out})


class ResubmitFileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, submission_id, file_type):
        submission = get_object_or_404(Submission, id=submission_id)

        if not admin_only_upload_test(request.user) and submission.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

        if not submission.resubmission_allowed:
            return Response({"detail": "Resubmission no longer allowed."}, status=400)

        new_file = request.FILES.get("file")
        if not new_file:
            return Response({"detail": "Missing file."}, status=400)

        old = submission.files.filter(file_type=f"{file_type}_raw").first()
        if not old:
            return Response({"detail": f"No existing {file_type}_raw file found."}, status=400)

        # compute count once
        current_resubmission_count = FileHistory.objects.filter(
            submission=submission,
            file_type__endswith="_raw"
        ).count() + 1

        old_file_history_path = archive_file_to_submission_history(
            submission, old.file, os.path.basename(old.file.name), f"{file_type}_raw", current_resubmission_count
        )

        cleaned_file_history_path = None
        if old.cleaned_file and old.cleaned_file.name:
            cleaned_file_history_path = archive_file_to_submission_history(
                submission, old.cleaned_file, os.path.basename(old.cleaned_file.name), f"{file_type}_cleaned", current_resubmission_count
            )
            old.cleaned_file.delete(save=False)
            old.cleaned_file = None

        FileHistory.objects.create(
            submission=submission,
            file_type=f"{file_type}_raw",
            old_file=old_file_history_path,
            cleaned_file=cleaned_file_history_path,
        )

        # assign new raw
        old.file = new_file

        warnings = False
        message = ""
        if file_type == "metadata":
            valid, warnings, message, delimiter, df = validate_and_save_csv(
                new_file, METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS
            )
            if valid and df is not None:
                mismatch, mismatch_msg = compare_metadata_with_uploaded_files(submission, df)
                if mismatch:
                    return Response({"ok": False, "detail": mismatch_msg}, status=400)

            if not valid:
                return Response({"ok": False, "detail": message}, status=400)

            if df is not None:
                cleaned = generate_cleaned_file(new_file.name, df)
                old.cleaned_file = cleaned

        old.save()

        if warnings:
            submission.metadata_warnings = message
            submission.save(update_fields=["metadata_warnings"])
            return Response({"ok": True, "warnings": True, "message": message})
        else:
            submission.resubmission_allowed = False
            submission.metadata_warnings = ""
            submission.save(update_fields=["resubmission_allowed", "metadata_warnings"])
            return Response({"ok": True, "warnings": False, "message": "File resubmitted successfully."})


class SubmissionSamplesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(Submission, id=submission_id)

        sample_ids = sorted(
            set(
                AnalysisResult.objects.filter(submission=submission, status="finished")
                .values_list("sample_id", flat=True)
            )
        )

        fastq_files_qs = UploadedFile.objects.filter(
            submission=submission,
            file_type="fastq",
        ).exclude(file="")

        antibiotics_files_qs = UploadedFile.objects.filter(
            submission=submission,
            file_type__in=["antibiotics_raw", "antibiotics_cleaned"],
        ).exclude(file="")

        fastq_files = [
            {
                "name": os.path.basename(f.file.name),
                "sample_id": f.sample_id or "",
                "file_type": f.file_type,
            }
            for f in fastq_files_qs
            if f.file and f.file.name
        ]

        antibiotics_files = [
            {
                "name": os.path.basename(f.file.name),
                "sample_id": f.sample_id or "",
                "file_type": f.file_type,
            }
            for f in antibiotics_files_qs
            if f.file and f.file.name
        ]

        payload = {
            "submission_id": submission.id,
            "sample_ids": sample_ids,
            "fastq_files": fastq_files,
            "antibiotics_files": antibiotics_files,
        }
        return Response(SubmissionSampleListSerializer(payload).data)


PREVIEWABLE_RESULT_FILE_EXTENSIONS = {".html", ".htm", ".csv", ".tsv", ".txt"}
MAX_PREVIEW_BYTES = 50 * 1024 * 1024


def _resolve_result_root_candidates(raw_directory: str) -> list[Path]:
    project_root = Path(__file__).resolve().parents[2]
    normalized = str(raw_directory or "").strip()
    normalized_unix = normalized.replace("\\", "/")

    candidates: list[Path] = []

    if normalized:
        raw_path = Path(normalized).expanduser()
        if raw_path.is_absolute():
            candidates.append(raw_path)
        else:
            candidates.append((project_root / raw_path))

        marker = "/runs/all_results/"
        if marker in normalized_unix:
            tail = normalized_unix.split(marker, 1)[1].lstrip("/")
            if tail:
                candidates.append(project_root / "runs" / "all_results" / tail)

        # Fallback: map by terminal directory name (sample folder)
        name = raw_path.name
        if name:
            candidates.append(project_root / "runs" / "all_results" / name)

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _directory_has_files(directory: Path) -> bool:
    return any(entry.is_file() for entry in directory.rglob("*"))


def _discover_result_root_by_sample(sample_id: str) -> Path | None:
    project_root = Path(__file__).resolve().parents[2]
    runs_root = project_root / "runs"
    if not runs_root.exists() or not runs_root.is_dir():
        return None

    # Prefer top-level batch folders like runs/jena_batch/<sample_id>
    for batch_dir in sorted(runs_root.iterdir(), key=lambda p: p.name.lower()):
        if not batch_dir.is_dir():
            continue

        direct_candidate = batch_dir / sample_id
        if direct_candidate.exists() and direct_candidate.is_dir() and _directory_has_files(direct_candidate):
            return direct_candidate.resolve()

        # Also support one extra nesting level like runs/all_batches/<batch>/<sample_id>
        try:
            nested_dirs = sorted(batch_dir.iterdir(), key=lambda p: p.name.lower())
        except PermissionError:
            continue

        for nested in nested_dirs:
            if not nested.is_dir():
                continue
            nested_candidate = nested / sample_id
            if nested_candidate.exists() and nested_candidate.is_dir() and _directory_has_files(nested_candidate):
                return nested_candidate.resolve()

    return None


def _get_result_root_for_sample(submission: Submission, sample_id: str) -> Path:
    analysis = (
        AnalysisResult.objects.filter(submission=submission, sample_id=sample_id)
        .exclude(result_directory__in=["", "not_set"])
        .order_by("-id")
        .first()
    )
    if not analysis:
        raise FileNotFoundError("No result directory found for this sample.")

    existing_dirs: list[Path] = []
    for candidate in _resolve_result_root_candidates(analysis.result_directory):
        resolved = candidate.resolve()
        if resolved.exists() and resolved.is_dir():
            existing_dirs.append(resolved)
        if resolved.exists() and resolved.is_dir() and _directory_has_files(resolved):
            corrected = str(resolved)
            if analysis.result_directory != corrected:
                analysis.result_directory = corrected
                analysis.save(update_fields=["result_directory"])
            return resolved

    discovered = _discover_result_root_by_sample(sample_id)
    if discovered:
        corrected = str(discovered)
        if analysis.result_directory != corrected:
            analysis.result_directory = corrected
            analysis.save(update_fields=["result_directory"])
        return discovered

    # If an existing directory is found but empty, keep using it so UI can still render an empty tree.
    if existing_dirs:
        return existing_dirs[0]

    raise FileNotFoundError("Result directory does not exist on disk.")


def _safe_result_file_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    candidate.relative_to(root)
    return candidate


# Pipeline stage order, used to sort result folders instead of alphabetically.
# Folders not listed here (e.g. "main", "tools", reference files) fall back to
# alphabetical order after the known stages.
PIPELINE_STAGE_ORDER = [
    "gather",
    "qc",
    "assembler",
    "annotator",
    "sketcher",
    "mlst",  # Sequence Typing
    "amrfinderplus",  # Antibiotic Resistance
    "merlin",
]
PIPELINE_STAGE_PRIORITY = {name: idx for idx, name in enumerate(PIPELINE_STAGE_ORDER)}
OPTIONAL_PIPELINE_STAGES = {"merlin"}


def _stage_dirs_for_sample(root: Path) -> dict[str, Path]:
    """
    Finds each pipeline stage's output folder under a sample's result root,
    regardless of nesting (stages live under both main/ and tools/).
    """
    found: dict[str, Path] = {}
    for child in root.rglob("*"):
        if not child.is_dir():
            continue
        name_lower = child.name.lower()
        if name_lower in PIPELINE_STAGE_PRIORITY and name_lower not in found:
            found[name_lower] = child
    return found


# Stages whose underlying tool is fixed by Bactopia's own design, not
# dependent on platform/species - safe to label statically.
STATIC_STAGE_TOOLS = {
    "gather": "FASTQ-Scan",
    "sketcher": "Mash + Sourmash",
    "mlst": "MLST",
    "amrfinderplus": "AMRFinderPlus",
}

# Merlin dispatches different species-specific typing tools per sample; these
# live as their own top-level tools/<name>/ folders (not nested under a
# "merlin" folder), alongside mlst/amrfinderplus which get their own columns.
MERLIN_EXCLUDED_TOOL_DIRS = {"mlst", "amrfinderplus", "mashdist"}
MERLIN_TOOL_DISPLAY_NAMES = {
    "kleborate": "Kleborate",
    "clermontyping": "ClermonTyping",
    "shigatyper": "ShigaTyper",
    "shigeifinder": "ShigEiFinder",
    "stecfinder": "STECFinder",
    "shigapass": "ShigaPass",
    "ectyper": "ECTyper",
}


def _merlin_display_name(folder_name: str) -> str:
    return MERLIN_TOOL_DISPLAY_NAMES.get(folder_name.lower(), folder_name.replace("_", " ").title())


def _merlin_tools_for_sample(root: Path) -> tuple[Path | None, str | None]:
    tools_dir = next((child for child in root.rglob("tools") if child.is_dir()), None)
    if not tools_dir:
        return None, None

    found = [
        d for d in tools_dir.iterdir()
        if d.is_dir() and d.name.lower() not in MERLIN_EXCLUDED_TOOL_DIRS
    ]
    if not found:
        return None, None

    label = " + ".join(_merlin_display_name(d.name) for d in sorted(found, key=lambda d: d.name.lower()))
    return found[0], label


def _detect_assembler_tool(stage_dir: Path) -> str | None:
    """
    Reports the tool Bactopia's assembler stage actually invokes (Shovill for
    short reads, Dragonflye for long reads, Unicycler for hybrid) - not the
    inner engine that wrapper happens to pick (e.g. Shovill choosing Skesa
    internally), which is an implementation detail of the wrapper itself.
    """
    logs_dir = stage_dir / "logs"
    if not logs_dir.is_dir():
        return None

    log_names = {p.name.lower() for p in logs_dir.glob("*.log")}
    if any("shovill" in name for name in log_names):
        return "Shovill"
    if any("dragonflye" in name for name in log_names):
        return "Dragonflye"
    if any("unicycler" in name for name in log_names):
        return "Unicycler"
    return None


def _detect_qc_tools(stage_dir: Path) -> str | None:
    summary_dir = stage_dir / "summary"
    if not summary_dir.is_dir():
        return None

    names = [p.name.lower() for p in summary_dir.iterdir()]
    tools_found = []
    if any("fastp" in n for n in names):
        tools_found.append("Fastp")
    if any("nanoplot" in n for n in names):
        tools_found.append("NanoPlot")
    return " + ".join(tools_found) if tools_found else None


def _detect_annotator_tool(stage_dir: Path) -> str | None:
    for child in stage_dir.iterdir():
        if child.is_dir() and child.name.lower() in {"prokka", "bakta"}:
            return child.name.capitalize()
    return None


def _detect_stage_tool(stage: str, stage_dir: Path) -> str | None:
    if stage in STATIC_STAGE_TOOLS:
        return STATIC_STAGE_TOOLS[stage]
    if stage == "assembler":
        return _detect_assembler_tool(stage_dir)
    if stage == "qc":
        return _detect_qc_tools(stage_dir)
    if stage == "annotator":
        return _detect_annotator_tool(stage_dir)
    return None


def _sample_metadata_lookup(submission) -> dict:
    """
    Maps sample_id -> {"species": ..., "platform": ...} from the submission's
    own submitted metadata (user-declared, not Bactopia-computed) - the only
    reliable source for sequencing technology, since Bactopia's own report
    doesn't distinguish e.g. PacBio from ONT (both show up as "ont").
    """
    df = _get_submission_metadata_df(submission)
    if df is None or "sample identifier" not in df.columns:
        return {}

    def platform_for_row(row):
        # Prefer an explicit platform column, but it's often left blank even
        # when it exists - fall back to whichever platform-specific file
        # column is actually populated for this sample.
        platform = _normalize_text(row.get("sequencing platform")) if "sequencing platform" in df.columns else None
        if platform:
            return platform
        if _normalize_text(row.get("illumina r1")) or _normalize_text(row.get("illumina r2")):
            return "Illumina"
        if "pacbio" in df.columns and _normalize_text(row.get("pacbio")):
            return "PacBio"
        if "nanopore" in df.columns and _normalize_text(row.get("nanopore")):
            return "Nanopore"
        return None

    lookup = {}
    for _, row in df.iterrows():
        sample_id = _normalize_text(row.get("sample identifier"))
        if not sample_id:
            continue
        lookup[sample_id] = {
            "species": _normalize_text(row.get("isolate species")),
            "platform": platform_for_row(row),
        }
    return lookup


class SubmissionResultsDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(Submission, id=submission_id)

        sample_ids = sorted(
            set(
                AnalysisResult.objects.filter(submission=submission, status="finished")
                .values_list("sample_id", flat=True)
            )
        )
        report_rows = load_bactopia_report()
        metadata_lookup = _sample_metadata_lookup(submission)

        succeeded = failed = pending = 0
        samples_payload = []

        for sample_id in sample_ids:
            report = report_rows.get(sample_id)
            if report is None:
                rank, reason, report_species = None, None, None
                pending += 1
            elif report["rank"] == "exclude":
                rank, reason, report_species = report["rank"], report["reason"], report.get("species")
                failed += 1
            else:
                rank, reason, report_species = report["rank"], report["reason"], report.get("species")
                succeeded += 1

            submitted_meta = metadata_lookup.get(sample_id, {})
            species = report_species or submitted_meta.get("species")
            sequencing_technology = submitted_meta.get("platform")

            try:
                root = _get_result_root_for_sample(submission, sample_id)
                stage_dirs = _stage_dirs_for_sample(root)
            except FileNotFoundError:
                root = None
                stage_dirs = {}

            stages = {}
            for stage in PIPELINE_STAGE_ORDER:
                if stage == "merlin":
                    stage_dir, tool = (_merlin_tools_for_sample(root) if root else (None, None))
                else:
                    stage_dir = stage_dirs.get(stage)
                    tool = _detect_stage_tool(stage, stage_dir) if stage_dir else None

                stages[stage] = {
                    "available": stage_dir is not None,
                    "path": stage_dir.relative_to(root).as_posix() if stage_dir and root else None,
                    "optional": stage in OPTIONAL_PIPELINE_STAGES,
                    "tool": tool,
                }

            zip_name = f"{sample_id}_results.zip"
            zip_exists = bool(root) and (root / zip_name).is_file()

            samples_payload.append(
                {
                    "sample_id": sample_id,
                    "rank": rank,
                    "reason": reason,
                    "species": species,
                    "sequencing_technology": sequencing_technology,
                    "stages": stages,
                    "download": {
                        "available": zip_exists,
                        "filename": zip_name,
                    },
                }
            )

        return Response(
            {
                "submission_id": submission.id,
                "total": len(sample_ids),
                "succeeded": succeeded,
                "failed": failed,
                "pending": pending,
                "stage_order": PIPELINE_STAGE_ORDER,
                "samples": samples_payload,
            }
        )


class SubmissionSampleResultFilesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int, sample_id: str):
        submission = get_object_or_404(Submission, id=submission_id)

        try:
            root = _get_result_root_for_sample(submission, sample_id)
        except FileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=404)

        def sort_key(item: Path):
            name_lower = item.name.lower()
            priority = PIPELINE_STAGE_PRIORITY.get(name_lower, len(PIPELINE_STAGE_ORDER))
            return (item.is_file(), priority, name_lower)

        def build_tree(directory: Path):
            nodes = []
            children = sorted(directory.iterdir(), key=sort_key)
            for child in children:
                rel_path = child.relative_to(root).as_posix()
                node = {
                    "name": child.name,
                    "path": rel_path,
                    "type": "directory" if child.is_dir() else "file",
                }
                if child.is_dir():
                    node["children"] = build_tree(child)
                else:
                    node["size"] = child.stat().st_size
                nodes.append(node)
            return nodes

        return Response(
            {
                "submission_id": submission.id,
                "sample_id": sample_id,
                "result_root": root.name,
                "tree": build_tree(root),
            }
        )


class SubmissionSampleResultFileContentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int, sample_id: str):
        submission = get_object_or_404(Submission, id=submission_id)

        relative_path = (request.query_params.get("path") or "").strip()
        if not relative_path:
            return Response({"detail": "Query parameter 'path' is required."}, status=400)

        try:
            root = _get_result_root_for_sample(submission, sample_id)
            file_path = _safe_result_file_path(root, relative_path)
        except FileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=404)
        except ValueError:
            return Response({"detail": "Invalid file path."}, status=400)

        if not file_path.exists() or not file_path.is_file():
            return Response({"detail": "File not found."}, status=404)

        extension = file_path.suffix.lower()
        if extension in PREVIEWABLE_RESULT_FILE_EXTENSIONS:
            file_size = file_path.stat().st_size
            if file_size > MAX_PREVIEW_BYTES:
                return Response(
                    {
                        "detail": "File is too large to preview in browser.",
                        "download_only": True,
                    },
                    status=413,
                )

            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()

            mime_type = mimetypes.guess_type(file_path.name)[0] or "text/plain"
            return Response(
                {
                    "mode": "preview",
                    "name": file_path.name,
                    "path": file_path.relative_to(root).as_posix(),
                    "extension": extension,
                    "mime_type": mime_type,
                    "content": content,
                }
            )

        return FileResponse(
            file_path.open("rb"),
            as_attachment=True,
            filename=file_path.name,
        )


class SubmissionStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(Submission, id=submission_id)

        # Keep lightweight compatibility summary fields
        fastq_files = UploadedFile.objects.filter(submission=submission, file_type="fastq")
        sample_ids = sorted(set(f.sample_id for f in fastq_files if f.sample_id))

        # Count antibiotics files
        antibiotics_files = UploadedFile.objects.filter(
            submission=submission,
            file_type__in=["antibiotics_raw", "antibiotics_cleaned"]
        )

        metadata_statistics = submission.metadata_statistics or {}

        return Response({
            "submission_id": submission.id,
            "username": submission.user.username,
            "created_at": submission.created_at,
            "submission_type": submission.submission_type,
            "is_bulk_upload": submission.is_bulk_upload,
            "metadata_statistics": metadata_statistics,
            "total_samples": len(sample_ids),
            "sample_ids": sample_ids,
            "total_fastq_files": fastq_files.count(),
            "total_antibiotics_files": antibiotics_files.count(),
        })


class GlobalStatisticsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        global_stats = GlobalStatistics.objects.filter(singleton_key=1).first()
        if not global_stats:
            global_stats = recompute_global_statistics()

        return Response({
            "stats_version": global_stats.stats_version,
            "last_recomputed_at": global_stats.last_recomputed_at,
            "total_submissions": global_stats.total_submissions,
            "total_metadata_rows": global_stats.total_metadata_rows,
            "total_fastq_files": global_stats.total_fastq_files,
            "total_antibiotics_files": global_stats.total_antibiotics_files,
            "total_unique_sample_identifiers": global_stats.total_unique_sample_identifiers,
            "total_unique_isolate_species": global_stats.total_unique_isolate_species,
            "platform_counts": global_stats.platform_counts,
            "sir_counts": global_stats.sir_counts,
            "mic_numeric_values": global_stats.mic_numeric_values,
            "map_location_counts": global_stats.map_location_counts,
            "qc_rank_counts": global_stats.qc_rank_counts,
        })