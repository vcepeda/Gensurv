from rest_framework import serializers
from gensurvapp.models import *

# Upload serializer

class SingleUploadSerializer(serializers.Serializer):
    metadata_file = serializers.FileField(required=True)
    antibiotics_file = serializers.FileField(required=False, allow_null=True)
    fastq_files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        allow_empty=False
    )
    submit_to_pipeline = serializers.BooleanField(required=False, default=False)
    upload_start_time = serializers.FloatField(required=False)


class BulkUploadSerializer(serializers.Serializer):
    metadata_file = serializers.FileField(required=True)
    antibiotics_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )
    fastq_files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        allow_empty=False
    )
    submit_to_pipeline = serializers.BooleanField(required=False, default=False)
    upload_start_time = serializers.FloatField(required=False)

# Dashboard serializer

class UploadedFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    cleaned_file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = ["id", "file_type", "sample_id", "file_url", "cleaned_file_url"]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_cleaned_file_url(self, obj):
        if not obj.cleaned_file:
            return None
        request = self.context.get("request")
        url = obj.cleaned_file.url
        return request.build_absolute_uri(url) if request else url


class SubmissionDashboardRowSerializer(serializers.Serializer):
    username = serializers.CharField()
    submission_id = serializers.IntegerField()
    created_at = serializers.DateTimeField()

    metadata = serializers.DictField()  # { raw: {url,name}, cleaned:{url,name}, warnings, resub_count, can_resubmit }
    antibiotics = serializers.DictField()  # { files: [...], info: {...}, warnings }
    fastq = serializers.DictField()  # { grouped: {sample_id: [ {url,name} ] } , extra_warning }
    analysis = serializers.DictField()  # { statuses: {sample_id: "completed|failed|pending"} }
    deletion = serializers.DictField()  # { requested: bool }

class SubmissionSampleListSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()
    sample_ids = serializers.ListField(child=serializers.CharField())

