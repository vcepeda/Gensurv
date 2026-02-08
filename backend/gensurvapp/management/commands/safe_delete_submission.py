# safe_delete_submission.py

from django.core.management.base import BaseCommand
from gensurvapp.models import Submission, SampleFile, UploadedFile, FileHistory, BactopiaResult, PlasmidIdentResult
import os
import shutil

class Command(BaseCommand):
    help = 'Safely delete a Submission and move associated files to a trash folder (with confirmation & dry-run).'

    def add_arguments(self, parser):
        parser.add_argument('submission_id', type=int, help='ID of the Submission to delete')
        parser.add_argument('--trash_dir', type=str, default='media/deleted_submissions/', help='Directory to move files to')
        parser.add_argument('--dry-run', action='store_true', help='Simulate deletion without actually deleting or moving files')
        parser.add_argument('--force', action='store_true', help='Skip confirmation and force deletion')

    def handle(self, *args, **options):
        submission_id = options['submission_id']
        trash_dir = options['trash_dir']
        dry_run = options['dry_run']
        force = options['force']

        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            self.stderr.write(f"❌ Submission with ID {submission_id} does not exist.")
            return

        self.stdout.write(f"🚀 Safe deleting Submission ID {submission_id} for user {submission.user.username}")
        self.stdout.write(f"📅 Created at: {submission.created_at}")
        self.stdout.write(f"🗂 Trash directory: {trash_dir}")
        if dry_run:
            self.stdout.write(f"⚠️ DRY-RUN mode enabled → no files will be moved or deleted.")
        
        if not force and not dry_run:
            confirm = input(f"⚠️ Are you sure you want to permanently delete Submission {submission_id}? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("❌ Aborted by user.")
                return

        if not dry_run:
            os.makedirs(trash_dir, exist_ok=True)

        # SampleFile
        for sample_file in submission.sample_files.all():
            self._move_file(sample_file.file.path, trash_dir, dry_run)
            if not dry_run:
                sample_file.delete()

        # UploadedFile
        for uploaded_file in submission.uploadedfile_set.all():
            if uploaded_file.file:
                self._move_file(uploaded_file.file.path, trash_dir, dry_run)
            if uploaded_file.cleaned_file:
                self._move_file(uploaded_file.cleaned_file.path, trash_dir, dry_run)
            if not dry_run:
                uploaded_file.delete()

        # FileHistory
        for history_file in FileHistory.objects.filter(submission=submission):
            self._move_file(history_file.old_file.path, trash_dir, dry_run)
            if history_file.cleaned_file:
                self._move_file(history_file.cleaned_file.path, trash_dir, dry_run)
            if not dry_run:
                history_file.delete()

        # BactopiaResult / PlasmidIdentResult
        bactopia_count = BactopiaResult.objects.filter(submission=submission).count()
        plasmidident_count = PlasmidIdentResult.objects.filter(submission=submission).count()

        if not dry_run:
            BactopiaResult.objects.filter(submission=submission).delete()
            PlasmidIdentResult.objects.filter(submission=submission).delete()

        self.stdout.write(f"🧬 BactopiaResults deleted: {bactopia_count}")
        self.stdout.write(f"🧬 PlasmidIdentResults deleted: {plasmidident_count}")

        # Final Submission delete
        if not dry_run:
            submission.delete()
            self.stdout.write(f"✅ Submission {submission_id} deleted.")
        else:
            self.stdout.write(f"✅ Would delete Submission {submission_id} (dry-run).")

    def _move_file(self, path, trash_dir, dry_run):
        if os.path.exists(path):
            filename = os.path.basename(path)
            dest_path = os.path.join(trash_dir, filename)
            if dry_run:
                self.stdout.write(f"   [DRY-RUN] Would move file: {path} → {dest_path}")
            else:
                shutil.move(path, dest_path)
                self.stdout.write(f"   🗂 Moved file: {path} → {dest_path}")
        else:
            self.stderr.write(f"⚠️ File not found: {path}")


