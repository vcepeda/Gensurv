from django import forms

class CreateNewList(forms.Form):
    name = forms.CharField(label="Name", max_length=200)
    check = forms.BooleanField(required=False)


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for handling multiple file uploads."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Custom field for processing multiple file uploads."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """Validate multiple files if provided."""
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)

class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100)


class UploadFileForm(forms.Form):
    file = forms.FileField()


class FileUploadForm(forms.Form):
    """Form to handle multiple FASTQ and metadata files."""
    metadata_file = forms.FileField(label="Metadata File", required=True)
    antibiotics_file = forms.FileField(label="Antibiotics Testing File", required=False)
    fastq_files = MultipleFileField(label="FASTQ File(s)", required=False)



class SingleUploadForm(forms.Form):
    """Form for single sample uploads."""
    metadata_file = forms.FileField(label="Metadata File", required=True)
    antibiotics_file = forms.FileField(label="Antibiotics File", required=False)
    fastq_files = MultipleFileField(label="FASTQ File(s)", required=True)

class BulkUploadForm(forms.Form):
    """Form for bulk uploads."""
    metadata_file = forms.FileField(label="Metadata File (CSV)", required=True)
    antibiotics_files = MultipleFileField(
        label="Antibiotics Files (maximun 1 per sample)", required=False
    )
    fastq_files = MultipleFileField(
        label="FASTQ Files (1 or more per sample)", required=True
    )
