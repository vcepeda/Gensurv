from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from gensurvapp.models import Submission, UploadedFile, FileHistory
import os
from django.conf import settings
from collections import defaultdict
import json

User = get_user_model()

class Command(BaseCommand):
    help = "Restore a deleted Submission + UploadedFiles (and optionally FileHistory). Keeps original Submission ID."

    def add_arguments(self, parser):
        parser.add_argument('submission_id', type=int, help='Original Submission ID to restore')
        parser.add_argument('username', type=str, help='Username of owner')
        parser.add_argument('--with-history', action='store_true', help='Also restore FileHistory entries if available')

    def handle(self, *args, **options):
        submission_id = options['submission_id']
        username = options['username']

        media_root = settings.MEDIA_ROOT
        submission_folder = os.path.join(media_root, 'submissions', username, f'submission_{submission_id}')
        backup_json_path = os.path.join(media_root, 'backups', username, f'submission_{submission_id}', 'submission_data.json')

        if not os.path.isdir(submission_folder):
            self.stderr.write(self.style.ERROR(f"❌ Folder not found: {submission_folder}"))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"❌ User '{username}' not found"))
            return

        if Submission.objects.filter(pk=submission_id).exists():
            self.stderr.write(self.style.ERROR(f"❌ Submission with ID {submission_id} already exists in DB. Cannot restore."))
            return

        # Load sample_id for FASTQ files from backup JSON
        sample_id_lookup = {}
        if os.path.exists(backup_json_path):
            with open(backup_json_path, 'r') as f:
                data = json.load(f)
                for entry in data:
                    if entry.get("model") == "gensurvapp.uploadedfile":
                        fields = entry["fields"]
                        if fields.get("file_type") == "fastq":
                            filename = os.path.basename(fields.get("file", ""))
                            sample_id_lookup[filename] = fields.get("sample_id", "unknown")

        with transaction.atomic():
            submission = Submission(
                pk=submission_id,
                user=user,
                metadata_file='',
                is_bulk_upload=True,
                resubmission_allowed=True
            )
            submission.save(force_insert=True)
            self.stdout.write(self.style.SUCCESS(f"✅ Created Submission ID {submission.id}"))

            # Map raw/cleaned files
            file_map = defaultdict(dict)
            for filename in os.listdir(submission_folder):
                if filename.startswith('cleaned_'):
                    raw_name = filename[len('cleaned_'):]
                    file_map[raw_name]['cleaned'] = filename
                else:
                    file_map[filename]['raw'] = filename

            # Restore UploadedFiles
            for raw_name, files in file_map.items():
                raw_filename = files.get('raw')
                cleaned_filename = files.get('cleaned')

                file_type = 'unknown'
                sample_id = 'unknown'

                guess_name = raw_filename or cleaned_filename
                guess_lower = guess_name.lower()

                if 'metadata' in guess_lower:
                    file_type = 'metadata_raw'
                    sample_id = 'metadata'
                elif 'antibiotics' in guess_lower:
                    file_type = 'antibiotics'
                    sample_id = 'antibiotics'
                elif guess_lower.endswith('.fastq') or guess_lower.endswith('.fastq.gz'):
                    file_type = 'fastq'
                    sample_id = sample_id_lookup.get(guess_name, 'unknown')

                raw_path = os.path.join('submissions', username, f'submission_{submission_id}', raw_filename) if raw_filename else ''
                cleaned_path = os.path.join('submissions', username, f'submission_{submission_id}', cleaned_filename) if cleaned_filename else None

                UploadedFile.objects.create(
                    submission=submission,
                    file=raw_path,
                    cleaned_file=cleaned_path,
                    file_type=file_type,
                    sample_id=sample_id
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  ➜ Added: raw={raw_filename}, cleaned={cleaned_filename}, type={file_type}, sample={sample_id}"
                ))

            # Set metadata_file
            try:
                meta_file = UploadedFile.objects.filter(submission=submission, file_type='metadata_raw').first()
                if meta_file:
                    submission.metadata_file = meta_file.file
                    submission.save()
                    self.stdout.write(self.style.SUCCESS(f"📄 Submission.metadata_file set to: {meta_file.file}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No metadata_raw file found to set on Submission."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error setting metadata_file: {e}"))

            # Restore FileHistory
            if options['with_history']:
                self.stdout.write(self.style.WARNING(f"⚙️ Restoring FileHistory for Submission {submission_id}"))

                history_root = os.path.join(submission_folder, 'history')
                if not os.path.isdir(history_root):
                    self.stdout.write(self.style.WARNING(f"⚠️ No history folder found at: {history_root}"))
                else:
                    resub_folders = sorted([d for d in os.listdir(history_root) if d.startswith('resubmission_')])

                    for resub_id, resub_dir in enumerate(resub_folders, start=1):
                        resub_path = os.path.join(history_root, resub_dir)
                        resub_file_map = defaultdict(dict)

                        for f in os.listdir(resub_path):
                            if f.startswith('cleaned_'):
                                raw_name = f[len('cleaned_'):]
                                resub_file_map[raw_name]['cleaned'] = f
                            else:
                                resub_file_map[f]['raw'] = f

                        for raw_filename, files in resub_file_map.items():
                            cleaned_filename = files.get('cleaned')
                            file_type = 'metadata_raw' if 'metadata' in raw_filename.lower() else 'antibiotics_raw'

                            old_path = os.path.join('submissions', username, f'submission_{submission_id}', 'history', resub_dir, raw_filename)
                            cleaned_path = os.path.join('submissions', username, f'submission_{submission_id}', 'history', resub_dir, cleaned_filename) if cleaned_filename else None
                            cleaned_abs = os.path.join(settings.MEDIA_ROOT, cleaned_path) if cleaned_path else None
                            cleaned_exists = os.path.exists(cleaned_abs) if cleaned_abs else False

                            FileHistory.objects.create(
                                submission=submission,
                                file_type=file_type,
                                old_file=old_path,
                                cleaned_file=cleaned_path if cleaned_exists else None
                            )
                            self.stdout.write(self.style.SUCCESS(f"  ➜ Restored {resub_dir}: raw={raw_filename}, cleaned={cleaned_filename}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Restore complete. Submission ID: {submission.id}"))
