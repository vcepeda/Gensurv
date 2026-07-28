import csv
import gzip
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Import the valid sample ID roster from a CoGDat_<timestamp>.csv(.gz) export, "
        "replacing whatever roster is currently stored. Used to validate FASTQ filenames "
        "on COGDAT's fastq-only uploads, since those have no metadata file of their own."
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to a CoGDat_<timestamp>.csv or .csv.gz export")

    def handle(self, *args, **options):
        from gensurvapp.models import CogdatSampleId

        path = Path(options["file"]).expanduser().resolve()
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if "sampleID" not in (reader.fieldnames or []):
                raise CommandError(f"'sampleID' column not found in {path}. Columns seen: {reader.fieldnames}")
            sample_ids = sorted({row["sampleID"].strip() for row in reader if row.get("sampleID", "").strip()})

        if not sample_ids:
            raise CommandError(f"No sample IDs found in {path}.")

        with transaction.atomic():
            CogdatSampleId.objects.all().delete()
            CogdatSampleId.objects.bulk_create(
                [CogdatSampleId(sample_id=sid) for sid in sample_ids]
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(sample_ids)} COGDAT sample ID(s) from {path.name}."))
