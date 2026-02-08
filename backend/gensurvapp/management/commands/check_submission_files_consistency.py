import os
from gensurvapp.models import Submission, UploadedFile
from django.conf import settings

def check_submission_files_consistency(submission_id, username):
    print(f"\n🔍 Checking consistency for submission {submission_id} (user: {username})")

    # Get submission
    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        print(f"❌ Submission {submission_id} not found in DB")
        return

    # Files in DB
    db_files = set(
        os.path.basename(f.file.name)
        for f in UploadedFile.objects.filter(submission=submission)
    )
    print(f"📂 {len(db_files)} files in UploadedFile:")

    for f in sorted(db_files):
        print(f"   - {f}")

    # Files in media/submissions folder
    media_folder = os.path.join(settings.MEDIA_ROOT, 'submissions', username, f'submission_{submission_id}')
    if not os.path.isdir(media_folder):
        print(f"❌ Folder not found: {media_folder}")
        return

    media_files = set(os.listdir(media_folder))
    print(f"🗂️  {len(media_files)} files in media folder:")

    for f in sorted(media_files):
        print(f"   - {f}")

    # Compare:
    print("\n🔎 Differences:")

    missing_in_db = media_files - db_files
    if missing_in_db:
        print(f"⚠️  Files present in media but missing in DB ({len(missing_in_db)}):")
        for f in sorted(missing_in_db):
            print(f"   - {f}")
    else:
        print("✅ No files missing in DB")

    missing_in_media = db_files - media_files
    if missing_in_media:
        print(f"⚠️  Files present in DB but missing in media ({len(missing_in_media)}):")
        for f in sorted(missing_in_media):
            print(f"   - {f}")
    else:
        print("✅ No files missing in media")

# Example usage:
# check_submission_files_consistency(276, "admin")

