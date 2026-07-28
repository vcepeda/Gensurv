import csv
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from gensurvapp.models import AnalysisResult, Submission, UploadedFile


class Command(BaseCommand):
    help = (
        "Creates two new submissions directly from existing fastq files, "
        "bypassing the web upload flow entirely - one with only the Illumina "
        "reads, one with only the Nanopore reads, for samples that were "
        "originally run as a single Bactopia 'hybrid' (combined) analysis. "
        "Reads the same sample sheet used for the original hybrid run (only "
        "rows with runtype=hybrid are used) to find each sample's r1/r2 "
        "(Illumina) and extra (Nanopore) file paths. Copies those files into "
        "each new submission's own media folder and creates UploadedFile + "
        "AnalysisResult rows (status='pending') for each sample, exactly "
        "like a normal upload would - so both submissions show up on the "
        "Dashboard immediately, with no results until Bactopia is actually "
        "run against each split and `link_bactopia_run` connects the output. "
        "Dry-run by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "sample_sheet", type=str,
            help="Path to the original hybrid sample sheet, e.g. /mnt/storage/ahcepev1/Bactopia-runs/freiburg.tsv",
        )
        parser.add_argument("--username", type=str, required=True, help="Username to own both new submissions, e.g. SandraReuter")
        parser.add_argument("--submission-type", type=str, default="bacteria", help="Submission type to set on both new submissions (default: bacteria)")
        parser.add_argument("--only", choices=["illumina", "ont"], default=None, help="Only create the Illumina-only or Nanopore-only submission (default: both). Useful to resume after a partial/interrupted run.")
        parser.add_argument("--apply", action="store_true", help="Actually create the submissions and copy files. Without this, only reports what would happen.")

    def handle(self, *args, **options):
        sheet_path = options["sample_sheet"]
        username = options["username"]
        submission_type = options["submission_type"]
        apply_changes = options["apply"]

        if not os.path.isfile(sheet_path):
            raise CommandError(f"Sample sheet not found: {sheet_path}")

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No user found with username={username!r}")

        with open(sheet_path, newline="") as f:
            rows = [row for row in csv.DictReader(f, delimiter="\t") if (row.get("runtype") or "").strip() == "hybrid"]

        if not rows:
            raise CommandError(f"No rows with runtype=hybrid found in {sheet_path}")

        self.stdout.write(f"Found {len(rows)} hybrid sample(s) in {sheet_path}.")

        missing = []
        for row in rows:
            for col in ("r1", "extra"):
                path = (row.get(col) or "").strip()
                if not path or not os.path.isfile(path):
                    missing.append(f"{row['sample']} ({col}): {path or '(empty)'}")
        if missing:
            raise CommandError("Aborting - missing or unreadable source file(s):\n  " + "\n  ".join(missing))

        only = options["only"]
        all_specs = [
            {"key": "illumina", "label": "Illumina-only", "read_cols": ["r1", "r2"]},
            {"key": "ont", "label": "Nanopore-only", "read_cols": ["extra"]},
        ]
        specs = [s for s in all_specs if only is None or s["key"] == only]

        for spec in specs:
            self.stdout.write("")
            self.stdout.write(f"=== {spec['label']} submission ===")

            if not apply_changes:
                self.stdout.write(
                    f"  [DRY RUN] Would create Submission(user={username}, "
                    f"submission_type={submission_type}, is_bulk_upload=True)"
                )
                for row in rows:
                    for col in spec["read_cols"]:
                        path = (row.get(col) or "").strip()
                        if path:
                            self.stdout.write(
                                f"    would copy: {path} -> "
                                f"submissions/{slugify(username)}/submission_<new_id>/{os.path.basename(path)} "
                                f"(sample_id={row['sample']})"
                            )
                    self.stdout.write(f"    would create AnalysisResult(sample_id={row['sample']}, status=pending)")
                continue

            with transaction.atomic():
                submission = Submission.objects.create(
                    user=user,
                    submission_type=submission_type,
                    is_bulk_upload=True,
                    submit_to_pipeline=False,
                )

                dest_dir = Path(settings.MEDIA_ROOT) / "submissions" / slugify(username) / f"submission_{submission.id}"
                dest_dir.mkdir(parents=True, exist_ok=True)

                for row in rows:
                    sample_id = row["sample"]
                    for col in spec["read_cols"]:
                        src_path = (row.get(col) or "").strip()
                        if not src_path:
                            continue
                        dest_path = dest_dir / os.path.basename(src_path)
                        shutil.copy2(src_path, dest_path)

                        rel_path = os.path.join("submissions", slugify(username), f"submission_{submission.id}", os.path.basename(src_path))
                        UploadedFile.objects.create(
                            submission=submission,
                            file=rel_path,
                            file_type="fastq",
                            sample_id=sample_id,
                        )
                        self.stdout.write(f"  copied: {src_path}\n    -> {dest_path}")

                    AnalysisResult.objects.create(
                        submission=submission,
                        sample_id=sample_id,
                        status="pending",
                    )

            self.stdout.write(self.style.SUCCESS(
                f"Created submission {submission.id} ({spec['label']}) with {len(rows)} sample(s), status=pending."
            ))
