import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from gensurvapp.models import Submission
from gensurvapp.utils import validate_and_save_csv, generate_cleaned_file
from gensurvapp.constants import METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS, ANTIBIOTICS_COLUMNS
from gensurvapp.services.global_stats_service import recompute_global_statistics
from gensurvapp.management.commands.server_upload import ServerFile


class Command(BaseCommand):
    help = (
        "Recover missing physical files for a Submission whose DB rows are still "
        "intact (e.g. files were deleted from disk but the Submission/UploadedFile "
        "rows were not - use restore_submission instead if the rows are also gone). "
        "Finds each UploadedFile's original filename inside --source-dir (searched "
        "recursively), copies raw files back to their exact original path, and "
        "regenerates cleaned_ metadata/antibiotics files by re-running the normal "
        "validation logic. Since source files may have been edited since the "
        "original upload, the resulting warnings can differ from what's stored on "
        "the Submission - this command always reports any difference, and only "
        "writes anything to disk/DB when --apply is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument('submission_id', type=int)
        parser.add_argument('--source-dir', required=True, nargs='+', help='One or more directories to search for original raw files (searched recursively by filename). Earlier dirs take priority on name collisions.')
        parser.add_argument('--apply', action='store_true', help='Actually copy files and update DB. Without this, only reports what would happen.')

    def handle(self, *args, **options):
        submission_id = options['submission_id']
        source_dirs = options['source_dir']
        apply_changes = options['apply']

        try:
            submission = Submission.objects.get(pk=submission_id)
        except Submission.DoesNotExist:
            raise CommandError(
                f"Submission {submission_id} does not exist in the DB - "
                f"this command only handles the case where the Submission row "
                f"survived and only its files are missing. Use restore_submission "
                f"if the row itself needs recreating."
            )

        index = {}
        for source_dir in source_dirs:
            if not os.path.isdir(source_dir):
                raise CommandError(f"Source dir not found: {source_dir}")
            for root, _, files in os.walk(source_dir):
                for fname in files:
                    index.setdefault(fname, os.path.join(root, fname))

        uploaded_files = list(submission.files.all())
        self.stdout.write(
            f"Submission {submission_id} ({submission.user.username}, "
            f"created {submission.created_at}, bulk={submission.is_bulk_upload}), "
            f"{len(uploaded_files)} tracked file(s)."
        )

        max_rows = None if submission.is_bulk_upload else 1

        missing_sources = []
        plan = []  # (uploaded_file, dest_abs, src_path, cleaned_dest_abs, cleaned_content)
        new_metadata_warning = None  # (has_warning, message)
        new_antibiotics_warnings = []

        for uf in uploaded_files:
            rel_path = uf.file.name
            basename = os.path.basename(rel_path)
            dest_abs = os.path.join(settings.MEDIA_ROOT, rel_path)
            cleaned_dest_abs = os.path.join(settings.MEDIA_ROOT, uf.cleaned_file.name) if uf.cleaned_file else None

            raw_ok = os.path.exists(dest_abs)
            cleaned_ok = cleaned_dest_abs is None or (
                os.path.exists(cleaned_dest_abs) and os.path.getsize(cleaned_dest_abs) > 0
            )
            if raw_ok and cleaned_ok:
                self.stdout.write(f"  [already on disk] {rel_path}")
                continue

            src_path = index.get(basename)
            if not src_path:
                missing_sources.append(basename)
                self.stderr.write(self.style.ERROR(f"  [NOT FOUND in source] {basename}"))
                continue

            cleaned_content = None

            if uf.file_type == "metadata_raw":
                sf = ServerFile(src_path)
                try:
                    valid, warn, msg, delim, df = validate_and_save_csv(
                        sf, METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS,
                        submission_type=submission.submission_type, max_rows=max_rows,
                    )
                finally:
                    sf.close()
                if not valid:
                    raise CommandError(f"Metadata file '{basename}' no longer validates: {msg}")
                df.columns = df.columns.str.lower().str.strip()
                cleaned_content = generate_cleaned_file(basename, df)
                new_metadata_warning = (warn, msg if warn else "")

            elif uf.file_type == "antibiotics_raw":
                sf = ServerFile(src_path)
                try:
                    valid, warn, msg, delim, df = validate_and_save_csv(sf, ANTIBIOTICS_COLUMNS)
                finally:
                    sf.close()
                if not valid:
                    raise CommandError(f"Antibiotics file '{basename}' no longer validates: {msg}")
                df.columns = df.columns.str.lower().str.strip()
                cleaned_content = generate_cleaned_file(basename, df)
                if warn:
                    new_antibiotics_warnings.append(f"Sample '{uf.sample_id}': {msg}")

            # fastq files: copied as-is, no cleaning step exists for them.

            plan.append((uf, rel_path, dest_abs, src_path, cleaned_dest_abs, cleaned_content))

        if missing_sources:
            raise CommandError(
                f"Aborting - {len(missing_sources)} file(s) not found anywhere under "
                f"{', '.join(source_dirs)}: {', '.join(missing_sources)}"
            )

        if not plan:
            self.stdout.write(self.style.SUCCESS("Nothing to do - all files already present on disk."))
            return

        self.stdout.write("")
        self.stdout.write(f"{len(plan)} file(s) to restore:")
        for uf, rel_path, *_ in plan:
            self.stdout.write(f"  {uf.file_type:15s} {rel_path}")

        old_meta_warn = (submission.metadata_warnings or "").strip()
        old_ab_warn = (submission.antibiotics_warnings or "").strip()
        new_meta_warn_text = (new_metadata_warning[1] if new_metadata_warning else old_meta_warn).strip()
        new_ab_warn_text = "\n".join(new_antibiotics_warnings).strip()

        self.stdout.write("")
        if new_metadata_warning is not None and new_meta_warn_text != old_meta_warn:
            self.stdout.write(self.style.WARNING("Metadata warnings CHANGED vs. what's stored:"))
            self.stdout.write(f"  stored : {old_meta_warn!r}")
            self.stdout.write(f"  fresh  : {new_meta_warn_text!r}")
        if new_antibiotics_warnings and new_ab_warn_text != old_ab_warn:
            self.stdout.write(self.style.WARNING("Antibiotics warnings CHANGED vs. what's stored:"))
            self.stdout.write(f"  stored : {old_ab_warn!r}")
            self.stdout.write(f"  fresh  : {new_ab_warn_text!r}")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                "Dry run - nothing copied or changed. Re-run with --apply to write files and update warnings."
            ))
            return

        for uf, rel_path, dest_abs, src_path, cleaned_dest_abs, cleaned_content in plan:
            os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
            shutil.copy2(src_path, dest_abs)
            self.stdout.write(self.style.SUCCESS(f"  copied raw: {rel_path}"))
            if cleaned_content is not None and cleaned_dest_abs:
                os.makedirs(os.path.dirname(cleaned_dest_abs), exist_ok=True)
                data = cleaned_content.read()
                if isinstance(data, str):
                    data = data.encode("utf-8")
                with open(cleaned_dest_abs, "wb") as f:
                    f.write(data)
                self.stdout.write(self.style.SUCCESS(f"  wrote cleaned: {uf.cleaned_file.name}"))

        changed = False
        if new_metadata_warning is not None:
            has_warning, msg = new_metadata_warning
            submission.metadata_warnings = msg if has_warning else ""
            submission.resubmission_allowed = bool(has_warning) or submission.resubmission_allowed
            changed = True
        if new_antibiotics_warnings or old_ab_warn:
            submission.antibiotics_warnings = new_ab_warn_text
            changed = True

        if changed:
            submission.save()
            self.stdout.write(self.style.SUCCESS("Updated submission warning fields."))

        try:
            recompute_global_statistics()
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f"Global statistics recompute failed: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"Recovery complete for submission {submission_id}."))
