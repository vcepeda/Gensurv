# gensurvapp/scripts/check_submission_consistency.py

import os
from django.conf import settings
from gensurvapp.models import Submission, UploadedFile, FileHistory

def check_submission_files_consistency(submission_id):
    print(f"\n=== Checking UploadedFile consistency for submission {submission_id} ===")

    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        print(f"❌ Submission {submission_id} not found in DB")
        return

    db_files = set(
        os.path.basename(f.file.name) for f in UploadedFile.objects.filter(submission=submission)
    )

    submission_folder = os.path.join(settings.MEDIA_ROOT, 'submissions', submission.user.username, f'submission_{submission_id}')
    if not os.path.isdir(submission_folder):
        print(f"❌ Folder not found: {submission_folder}")
        return

    media_files = set(os.listdir(submission_folder))

    print(f"📂 {len(db_files)} files in UploadedFile:")
    for f in sorted(db_files):
        print(f"   - {f}")

    print(f"\n🗂️  {len(media_files)} files in media/submissions/...:")
    for f in sorted(media_files):
        print(f"   - {f}")

    missing_in_db = media_files - db_files
    missing_in_media = db_files - media_files

    print("\n🔎 Differences:")

    if missing_in_db:
        print(f"⚠️  Files present in media/submissions but missing in UploadedFile DB ({len(missing_in_db)}):")
        for f in sorted(missing_in_db):
            print(f"   - {f}")
    else:
        print("✅ No files missing in UploadedFile DB")

    if missing_in_media:
        print(f"⚠️  Files referenced in UploadedFile but missing in media/submissions ({len(missing_in_media)}):")
        for f in sorted(missing_in_media):
            print(f"   - {f}")
    else:
        print("✅ No files missing in media/submissions folder")

def check_submission_filehistory_consistency(submission_id):
    print(f"\n=== Checking FileHistory consistency for submission {submission_id} ===")

    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        print(f"❌ Submission {submission_id} not found in DB")
        return

    db_files = set()
    histories = FileHistory.objects.filter(submission=submission)
    for h in histories:
        if h.old_file:
            db_files.add(os.path.basename(h.old_file.name))
        if h.cleaned_file:
            db_files.add(os.path.basename(h.cleaned_file.name))

    media_folder = os.path.join(settings.MEDIA_ROOT, 'history')
    if not os.path.isdir(media_folder):
        print(f"❌ Folder not found: {media_folder}")
        return

    media_files = set(os.listdir(media_folder))

    print(f"📂 {len(db_files)} files in FileHistory:")
    for f in sorted(db_files):
        print(f"   - {f}")

    print(f"\n🗂️  {len(media_files)} files in media/history:")
    for f in sorted(media_files):
        print(f"   - {f}")

    missing_in_db = media_files - db_files
    missing_in_media = db_files - media_files

    print("\n🔎 Differences:")

    if missing_in_db:
        print(f"⚠️  Files present in media/history but missing in FileHistory DB ({len(missing_in_db)}):")
        for f in sorted(missing_in_db):
            print(f"   - {f}")
    else:
        print("✅ No files missing in FileHistory DB")

    if missing_in_media:
        print(f"⚠️  Files referenced in FileHistory but missing in media/history ({len(missing_in_media)}):")
        for f in sorted(missing_in_media):
            print(f"   - {f}")
    else:
        print("✅ No files missing in media/history folder")

