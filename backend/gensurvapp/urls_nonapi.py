from django.urls import path
from . import views_nonapi as views
from .views_nonapi import (
    home, impressum, research, contact, datenschutz, accessibility,
    success_page, sample_csv, download_sample_csv,
    download_antibiotics_csv, detailed_metadata_fields,
    upload_files, upload_files_dev, submission_results
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('impressum/', impressum, name='impressum'),
    path('contact/', contact, name='contact'),
    path('datenschutz/', datenschutz, name='datenschutz'),
    path('accessibility/', accessibility, name='accessibility'),
    path('research/', research, name='research'),
    path('upload/', upload_files, name='upload_files'),
    path('upload_dev/', upload_files_dev, name='upload_files_dev'),
    path('resubmit/<int:submission_id>/<str:file_type>/', views.resubmit_file_view, name='resubmit_file'),
    path("submission/<int:submission_id>/request-delete/", views.request_submission_deletion, name="request_submission_deletion"),
    path('help/', views.help_view, name='help'),
    path('success/', views.success_page, name='success_page'),
    path('download_sample_csv/', download_sample_csv, name='download_sample_csv'),
    path('download_antibiotics_csv/', download_antibiotics_csv, name='download_antibiotics_csv'),
    path('detailed_metadata_fields/', detailed_metadata_fields, name='detailed_metadata_fields'),
    path('about/', views.about, name='about'),  # Add this line
    path('dashboard/', views.user_dashboard, name='dashboard'),
    # NOT in old urls.py but in vue — add when views are ready:
    # path('search/', views.search, name='search'),
    # path('dashboard_search/', views.dashboard_and_search, name='dashboard_and_search'),
    path('submissions/', views.submission_list, name='submission_list'),
    path('submission/<int:submission_id>/sample/<str:sample_id>/details/', views.sample_all_results, name='sample_all_results'),
    path('submission/<int:submission_id>/results/', submission_results, name='submission_results'),
    path('submission/<int:submission_id>/sample/<str:sample_id>/', views.sample_results, name='sample_results'),
]

# Removed from original urls.py:
# path('bulk_upload/', views.bulk_upload, name='bulk_upload'),
# path('sample_csv/', sample_csv, name='sample_csv'),

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)