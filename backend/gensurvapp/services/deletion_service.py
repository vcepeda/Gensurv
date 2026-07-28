"""
Shared "safe delete" logic for submissions: moves associated files to a trash
directory (instead of destroying them outright) and removes the DB rows.

Used by both the safe_delete_submission management command (for manual/CLI
use, e.g. testing) and the Django admin bulk action - kept in one place so
the two never drift apart.
"""

import os
import shutil

from django.conf import settings
from django.utils.text import slugify

from gensurvapp.models import FileHistory, BactopiaResult, PlasmidIdentResult


def _move_file(path, trash_dir, dry_run, log):
    if not path or not os.path.exists(path):
        return
    filename = os.path.basename(path)
    dest_path = os.path.join(trash_dir, filename)
    if dry_run:
        log(f"   [DRY-RUN] Would move file: {path} -> {dest_path}")
    else:
        shutil.move(path, dest_path)
        log(f"   Moved file: {path} -> {dest_path}")


def safe_delete_submission(submission, trash_dir=None, dry_run=False, log=print):
    """
    Moves a submission's files (UploadedFile + FileHistory) to trash_dir and
    deletes its DB rows (UploadedFile, FileHistory, BactopiaResult,
    PlasmidIdentResult, then the Submission itself).
    """
    trash_dir = trash_dir or os.path.join(settings.MEDIA_ROOT, "deleted_submissions")
    # Each submission gets its own subfolder so files from different
    # submissions can never collide/overwrite each other by sharing a name.
    submission_trash_dir = os.path.join(trash_dir, f"submission_{submission.id}")

    if not dry_run:
        os.makedirs(submission_trash_dir, exist_ok=True)

    for uploaded_file in submission.files.all():
        if uploaded_file.file:
            _move_file(uploaded_file.file.path, submission_trash_dir, dry_run, log)
        if uploaded_file.cleaned_file:
            _move_file(uploaded_file.cleaned_file.path, submission_trash_dir, dry_run, log)
        if not dry_run:
            uploaded_file.delete()

    for history_file in FileHistory.objects.filter(submission=submission):
        if history_file.old_file:
            _move_file(history_file.old_file.path, submission_trash_dir, dry_run, log)
        if history_file.cleaned_file:
            _move_file(history_file.cleaned_file.path, submission_trash_dir, dry_run, log)
        if not dry_run:
            history_file.delete()

    bactopia_count = BactopiaResult.objects.filter(submission=submission).count()
    plasmidident_count = PlasmidIdentResult.objects.filter(submission=submission).count()

    if not dry_run:
        BactopiaResult.objects.filter(submission=submission).delete()
        PlasmidIdentResult.objects.filter(submission=submission).delete()

    log(f"BactopiaResults deleted: {bactopia_count}")
    log(f"PlasmidIdentResults deleted: {plasmidident_count}")

    # Original folder (submissions/<username>/submission_<id>/) is now empty
    # since every file it held has just been moved to trash above - remove it
    # rather than leaving an empty folder behind. Only removes it if it's
    # genuinely empty, never force-deletes anything unexpected still in there.
    original_dir = os.path.join(
        settings.MEDIA_ROOT, "submissions", slugify(submission.user.username), f"submission_{submission.id}"
    )
    if dry_run:
        if os.path.isdir(original_dir):
            log(f"   [DRY-RUN] Would remove original folder if empty: {original_dir}")
    else:
        if os.path.isdir(original_dir):
            try:
                os.rmdir(original_dir)
                log(f"   Removed empty original folder: {original_dir}")
            except OSError:
                log(f"   Original folder not empty, left in place: {original_dir}")

    if not dry_run:
        submission_id = submission.id
        submission.delete()
        log(f"Submission {submission_id} deleted.")
    else:
        log(f"Would delete Submission {submission.id} (dry-run).")
