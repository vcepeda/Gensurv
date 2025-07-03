import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from gensurvapp.models import Submission, UploadedFile, FileHistory

class Command(BaseCommand):
    help = 'Delete a submission, its UploadedFiles, FileHistory entries, and associated media files'

    def add_arguments(self, parser):
        parser.add_argument('submission_id', type=int)
        parser.add_argument('--delete-files', action='store_true', help='Also delete associated media files')
        parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')

    def handle(self, *args, **options):
        submission_id = options['submission_id']
        delete_files = options['delete_files']
        force = options['force']

        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"❌ Submission ID {submission_id} does not exist"))
            return

        self.stdout.write(self.style.WARNING(f"⚠️ You are about to delete submission {submission_id} by user '{submission.user.username}'"))
        if not force:
            confirm = input("Type 'yes' to confirm: ")
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.NOTICE("❌ Deletion cancelled"))
                return

        # Delete DB entries
        uploaded_files = UploadedFile.objects.filter(submission=submission)
        file_histories = FileHistory.objects.filter(submission=submission)

        file_histories.delete()
        uploaded_files.delete()
        submission.delete()

        self.stdout.write(self.style.SUCCESS(f"✅ Deleted submission {submission_id} and related DB entries"))

        if delete_files:
            folder = os.path.join(settings.MEDIA_ROOT, 'submissions', submission.user.username, f'submission_{submission_id}')
            if os.path.exists(folder):
                shutil.rmtree(folder)
                self.stdout.write(self.style.SUCCESS(f"🧹 Deleted media folder: {folder}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Media folder not found: {folder}"))

        self.stdout.write(self.style.SUCCESS("🎉 Deletion complete."))
