# gensurvapp/views_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import time
import logging

from .services.upload_service import handle_single_upload, handle_bulk_upload

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from gensurvapp.models import *
from gensurvapp.services.dashboard_service import build_dashboard_rows_for_user
from gensurvapp.services.global_stats_service import recompute_global_statistics
from gensurvapp.scripts.serializers import (
    SubmissionDashboardRowSerializer,
    SubmissionSampleListSerializer,
    SingleUploadSerializer,
    BulkUploadSerializer,
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
        submission_type = request.query_params.get("type", "bacteria")
        
        if submission_type not in ("bacteria", "virus"):
            return Response(
                {"success": False, "error": "Invalid type. Use 'bacteria' or 'virus'."},
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

            result = handle_single_upload(
                user=request.user,
                metadata_file=metadata_file,
                uploaded_antibiotics_file=antibiotics_file,
                fastq_files=fastq_files,
                submit_to_pipeline=submit_to_pipeline,
                submission_type=submission_type
            )

            response_data = {
                "success": True,
                "submission_id": result["submission_id"],
                "resubmission_allowed": result["resubmission_allowed"],
                "message": result["message"],
                "upload_duration": result["upload_duration"],
            }

            if upload_start_time:
                now = time.time()
                client_total = now - upload_start_time
                network_delay = client_total - result["upload_duration"]
                response_data.update({
                    "client_total_upload_time": client_total,
                    "network_delay": network_delay
                })

            return Response(response_data, status=status.HTTP_201_CREATED)

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
        submission_type = request.query_params.get("type", "bacteria")

        if submission_type not in ("bacteria", "virus"):
            return Response(
                {"success": False, "error": "Invalid type. Use 'bacteria' or 'virus'."},
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
            result = handle_bulk_upload(
                user=request.user,
                metadata_file=metadata_file,
                antibiotics_files=antibiotics_files,
                fastq_files=fastq_files,
                submit_to_pipeline=submit_to_pipeline,
                submission_type=submission_type
            )

            # Calculate timing metrics if client sent start time
            response_data = {
                "success": True,
                "submission_id": result["submission_id"],
                "resubmission_allowed": result["resubmission_allowed"],
                "message": result["message"],
                "upload_duration": result["upload_duration"],
            }

            if upload_start_time:
                now = time.time()
                client_total = now - upload_start_time
                network_delay = client_total - result["upload_duration"]
                response_data.update({
                    "client_total_upload_time": client_total,
                    "network_delay": network_delay
                })

            return Response(response_data, status=status.HTTP_201_CREATED)

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
        

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = build_dashboard_rows_for_user(request.user)

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

        bactopia_ids = BactopiaResult.objects.filter(submission=submission).values_list("sample_id", flat=True)
        plasmid_ids = PlasmidIdentResult.objects.filter(submission=submission).values_list("sample_id", flat=True)

        sample_ids = sorted(set(bactopia_ids) | set(plasmid_ids))

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


class SubmissionStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(Submission, id=submission_id)

        # Enforce ownership unless admin
        if not admin_only_upload_test(request.user) and submission.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=403)

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
        })