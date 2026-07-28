# safe_delete_submission.py

from django.core.management.base import BaseCommand
from gensurvapp.models import Submission
from gensurvapp.services.deletion_service import safe_delete_submission


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

        safe_delete_submission(submission, trash_dir=trash_dir, dry_run=dry_run, log=self.stdout.write)
