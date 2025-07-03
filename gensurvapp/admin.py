from django.contrib import admin
from .models import TodoItem, Item, Submission, UploadedFile
from .models import BactopiaResult, PlasmidIdentResult


# Register your models here.
admin.site.register(TodoItem)
admin.site.register(Item)

# Customize the admin display for the UploadedFile
class UploadedFileInline(admin.TabularInline):
    model = UploadedFile
    extra = 0  # Number of extra blank forms

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_metadata_file', 'get_antibiotics_file', 'created_at')
    inlines = [UploadedFileInline]  # Inline display for associated FASTQ files

    # Define methods to retrieve metadata_file and antibiotics_file
    def get_metadata_file(self, obj):
        return obj.metadata_file

    def get_antibiotics_file(self, obj):
        return obj.antibiotics_file

    # Set short descriptions for display in the admin
    get_metadata_file.short_description = 'Metadata File'
    get_antibiotics_file.short_description = 'Antibiotics File'

# Register Submission with customized admin
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(BactopiaResult)
admin.site.register(PlasmidIdentResult)
