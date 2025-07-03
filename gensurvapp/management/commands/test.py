from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from gensurvapp.models import Submission, UploadedFile, FileHistory
import os
from django.conf import settings
from collections import defaultdict
import glob
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

            file_map = defaultdict(dict)
            for filename in os.listdir(submission_folder):
                if filename.startswith('cleaned_'):
                    raw_name = filename[len('cleaned_'):]
                    file_map[raw_name]['cleaned'] = filename
                else:
                    file_map[filename]['raw'] = filename

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
                    sample_id = os.path.splitext(guess_name)[0]

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

            
            if options['with_history']:
                self.stdout.write(self.style.WARNING(f"⚙️ Restoring FileHistory for Submission {submission_id}"))

                history_root = os.path.join(submission_folder, 'history')
                if not os.path.isdir(history_root):
                    self.stdout.write(self.style.WARNING(f"⚠️ No history folder found at: {history_root}"))
                else:
                    resub_folders = sorted([d for d in os.listdir(history_root) if d.startswith('resubmission_')])

                    for resub_id, resub_dir in enumerate(resub_folders, start=1):
                        resub_path = os.path.join(history_root, resub_dir)
                        files = os.listdir(resub_path)

                        for f in files:
                            lower = f.lower()
                            file_type = 'metadata_raw' if 'metadata' in lower else 'antibiotics_raw'

                            old_path = os.path.join('submissions', username, f'submission_{submission_id}', 'history', resub_dir, f)
                            cleaned_candidate = f'cleaned_{f}'
                            cleaned_path = os.path.join('submissions', username, f'submission_{submission_id}', 'history', resub_dir, cleaned_candidate)

                            cleaned_abs_path = os.path.join(settings.MEDIA_ROOT, cleaned_path)
                            cleaned_file_exists = os.path.exists(cleaned_abs_path)

                            FileHistory.objects.create(
                                submission=submission,
                                file_type=file_type,
                                old_file=old_path,
                                cleaned_file=cleaned_path if cleaned_file_exists else None
                            )
                            self.stdout.write(self.style.SUCCESS(f"  ➜ Restored resubmission_{resub_id}: {f}"))


                

        self.stdout.write(self.style.SUCCESS(f"🎉 Restore complete. Submission ID: {submission.id}"))
