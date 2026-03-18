import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.auth import get_user_model

from gensurvapp.services.upload_service import handle_single_upload, handle_bulk_upload

User = get_user_model()


class ServerFile(File):
    """Wraps a server-side file to behave like an uploaded file."""
    def __init__(self, path):
        self._path = path
        self._file = open(path, 'rb')
        super().__init__(self._file, name=os.path.basename(path))

    def seek(self, pos):
        self._file.seek(pos)

    def close(self):
        self._file.close()


class Command(BaseCommand):
    help = 'Upload submission from server filesystem as a specific user'

    def add_arguments(self, parser):
        parser.add_argument('--user', required=True, help='Username to upload as')
        parser.add_argument('--metadata', required=True, help='Path to metadata CSV file')
        parser.add_argument('--fastq-dir', required=True, help='Directory containing FASTQ files')
        parser.add_argument('--antibiotics', nargs='*', default=[], help='Path(s) to antibiotics file(s)')
        parser.add_argument('--type', default='bacteria', choices=['bacteria', 'virus'], help='Submission type')
        parser.add_argument('--bulk', action='store_true', help='Use bulk upload (default: single)')
        parser.add_argument('--submit-to-pipeline', action='store_true', help='Submit to pipeline')

    def handle(self, *args, **options):
        # get user
        username = options['user']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")

        self.stdout.write(f"Uploading as user: {user.username}")

        # validate metadata file
        metadata_path = options['metadata']
        if not os.path.exists(metadata_path):
            raise CommandError(f"Metadata file not found: {metadata_path}")

        # collect fastq files
        fastq_dir = options['fastq_dir']
        if not os.path.isdir(fastq_dir):
            raise CommandError(f"FASTQ directory not found: {fastq_dir}")

        valid_extensions = ('.fastq', '.fq', '.bam', '.fastq.gz', '.fq.gz', '.bam.gz', '.bz2', '.xz', '.zip')
        fastq_paths = [
            os.path.join(fastq_dir, f)
            for f in os.listdir(fastq_dir)
            if f.lower().endswith(valid_extensions)
        ]

        if not fastq_paths:
            raise CommandError(f"No FASTQ files found in {fastq_dir}")

        self.stdout.write(f"Found {len(fastq_paths)} FASTQ file(s)")

        # collect antibiotics files
        antibiotics_paths = options['antibiotics'] or []
        for ab_path in antibiotics_paths:
            if not os.path.exists(ab_path):
                raise CommandError(f"Antibiotics file not found: {ab_path}")

        # open all files
        metadata_file = ServerFile(metadata_path)
        fastq_files = [ServerFile(p) for p in fastq_paths]
        antibiotics_files = [ServerFile(p) for p in antibiotics_paths]

        try:
            if options['bulk']:
                self.stdout.write("Running bulk upload...")
                result = handle_bulk_upload(
                    user=user,
                    metadata_file=metadata_file,
                    antibiotics_files=antibiotics_files,
                    fastq_files=fastq_files,
                    submission_type=options['type'],
                    submit_to_pipeline=options['submit_to_pipeline'],
                )
            else:
                self.stdout.write("Running single upload...")
                result = handle_single_upload(
                    user=user,
                    metadata_file=metadata_file,
                    uploaded_antibiotics_file=antibiotics_files[0] if antibiotics_files else None,
                    fastq_files=fastq_files,
                    submission_type=options['type'],
                    submit_to_pipeline=options['submit_to_pipeline'],
                )

            self.stdout.write(self.style.SUCCESS(
                f"Success! Submission ID: {result['submission_id']}\n"
                f"Message: {result['message']}\n"
                f"Duration: {result['upload_duration']:.2f}s"
            ))

        except ValueError as e:
            raise CommandError(f"Upload failed: {e}")
        finally:
            metadata_file.close()
            for f in fastq_files:
                f.close()
            for f in antibiotics_files:
                f.close()
