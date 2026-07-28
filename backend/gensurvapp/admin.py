from django.contrib import admin
from .models import Submission, UploadedFile
from .models import BactopiaResult, PlasmidIdentResult
from .models import CogdatSampleId
from .services.deletion_service import safe_delete_submission


# Register your models here.

# Customize the admin display for the UploadedFile
class UploadedFileInline(admin.TabularInline):
    model = UploadedFile
    extra = 0  # Number of extra blank forms

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_metadata_file', 'get_antibiotics_file', 'created_at', 'deletion_requested')
    list_filter = ('deletion_requested', 'submission_type')
    actions = ['safely_delete_selected']
    inlines = [UploadedFileInline]  # Inline display for associated FASTQ files

    # Define methods to retrieve metadata_file and antibiotics_file
    def get_metadata_file(self, obj):
        f = obj.files.filter(file_type='metadata_raw').first()
        return f.file.name if f and f.file else '-'

    def get_antibiotics_file(self, obj):
        f = obj.files.filter(file_type='antibiotics_raw').first()
        return f.file.name if f and f.file else '-'

    # Set short descriptions for display in the admin
    get_metadata_file.short_description = 'Metadata File'
    get_antibiotics_file.short_description = 'Antibiotics File'

    @admin.action(description="Safely delete selected submissions (moves files to trash, removes DB rows - cannot be undone from the UI)")
    def safely_delete_selected(self, request, queryset):
        submissions = list(queryset)
        for submission in submissions:
            safe_delete_submission(submission, log=lambda msg: None)
        self.message_user(request, f"Safely deleted {len(submissions)} submission(s). Files moved to media/deleted_submissions/.")

# Register Submission with customized admin
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(BactopiaResult)
admin.site.register(PlasmidIdentResult)


class CogdatSampleIdAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'imported_at')
    search_fields = ('sample_id',)
    ordering = ('sample_id',)

admin.site.register(CogdatSampleId, CogdatSampleIdAdmin)
