# gensurvapp/urls_api.py
from django.urls import path
from . import views

app_name = "gensurvapp_api"

urlpatterns = [
    # uploads (already exist)
    path("api/upload/single/", views.SingleUploadAPIView.as_view(), name="single-upload"),
    path("api/upload/bulk/", views.BulkUploadAPIView.as_view(), name="bulk-upload"),

    # dashboard
    path("api/dashboard/", views.DashboardAPIView.as_view(), name="dashboard"),

    # deletion
    path("api/submissions/<int:submission_id>/request-deletion/", views.RequestSubmissionDeletionAPIView.as_view(), name="request-submission-deletion"),

    # resubmission
    path("api/submissions/<int:submission_id>/resubmissions/<str:file_type>/", views.ResubmitFileAPIView.as_view(), name="resubmit-file"),
    path("api/submissions/<int:submission_id>/resubmissions/<str:file_type>/history/", views.ResubmissionHistoryAPIView.as_view(), name="resubmission-history"),

    # submission
    path("api/submissions/<int:submission_id>/samples/", views.SubmissionSamplesAPIView.as_view(), name="submission_samples_api"),

]