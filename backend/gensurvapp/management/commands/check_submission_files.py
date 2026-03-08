from django.core.management.base import BaseCommand
from gensurvapp.models import UploadedFile
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Check if the media files for a submission still exist on disk'

    def add_arguments(self, parser):
        parser.add_argument('submission_id', type=int)

    def handle(self, *args, **options):
        submission_id = options['submission_id']
        files = UploadedFile.objects.filter(submission_id=submission_id)

        if not files.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ No files in DB for submission {submission_id}"))
            return

        self.stdout.write(self.style.SUCCESS(f"📦 Found {files.count()} file(s) in DB"))
        missing = 0
        for f in files:
            file_path = f.file.path
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"❌ Missing: {file_path}"))
                missing += 1
            else:
                self.stdout.write(f"✅ {file_path}")

            if f.cleaned_file:
                cleaned = f.cleaned_file.path
                if not os.path.exists(cleaned):
                    self.stdout.write(self.style.ERROR(f"❌ Missing cleaned: {cleaned}"))
                    missing += 1
                else:
                    self.stdout.write(f"✅ {cleaned}")

        if missing == 0:
            self.stdout.write(self.style.SUCCESS("🎉 All files are present"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ {missing} missing file(s)"))
