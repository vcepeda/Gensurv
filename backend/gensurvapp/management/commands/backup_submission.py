from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from gensurvapp.models import Submission, UploadedFile, FileHistory
from django.conf import settings
import os
import shutil

class Command(BaseCommand):
    help = "Backup submission media files and database records."

    def add_arguments(self, parser):
        parser.add_argument("submission_id", type=int)
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        submission_id = options["submission_id"]
        username = options["username"]

        try:
            submission = Submission.objects.get(pk=submission_id)
        except Submission.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"❌ Submission {submission_id} not found."))
            return

        # Set paths
        src_folder = os.path.join(settings.MEDIA_ROOT, "submissions", username, f"submission_{submission_id}")
        backup_folder = os.path.join(settings.MEDIA_ROOT, "backups", username, f"submission_{submission_id}")
        os.makedirs(os.path.dirname(backup_folder), exist_ok=True)

        # 1. Copy media files
        if not os.path.exists(src_folder):
            self.stderr.write(self.style.ERROR(f"❌ Source folder not found: {src_folder}"))
            return

        if os.path.exists(backup_folder):
            self.stdout.write(self.style.WARNING(f"⚠️ Backup already exists. Overwriting: {backup_folder}"))
            shutil.rmtree(backup_folder)

        shutil.copytree(src_folder, backup_folder)
        self.stdout.write(self.style.SUCCESS(f"📦 Media files copied to: {backup_folder}"))

        # 2. Dump database objects
        files_qs = UploadedFile.objects.filter(submission_id=submission_id)
        history_qs = FileHistory.objects.filter(submission_id=submission_id)
        all_objs = [submission] + list(files_qs) + list(history_qs)

        json_data = serialize("json", all_objs, indent=2)

        with open(os.path.join(backup_folder, "submission_data.json"), "w") as f:
            f.write(json_data)

        self.stdout.write(self.style.SUCCESS("🗃️ Database records (Submission + UploadedFile + FileHistory) saved to submission_data.json"))

        # 3. Optionally copy history folder if it exists
        history_src = os.path.join(src_folder, "history")
        history_dest = os.path.join(backup_folder, "history")
        if os.path.exists(history_src):
            if os.path.exists(history_dest):
                shutil.rmtree(history_dest)  # avoid FileExistsError
            shutil.copytree(history_src, history_dest)
            self.stdout.write(self.style.SUCCESS(f"🗃️ History folder copied: {history_dest}"))


        self.stdout.write(self.style.SUCCESS(f"✅ Backup complete for submission {submission_id}"))
