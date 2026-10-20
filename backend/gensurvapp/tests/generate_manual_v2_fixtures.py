"""Generate and verify synthetic frontend-upload fixtures without saving submissions.

Run from the repository root:
  python backend/gensurvapp/tests/generate_manual_v2_fixtures.py
"""

import csv
import gzip
import os
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gensurv_project.settings")

import django

django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from gensurvapp.norovirus_v2_constants import NOROVIRUS_V2_METADATA_COLUMNS
from gensurvapp.services.upload_service_norovirus_v2 import validate_upload


def main():
    output = BACKEND.parent / "manual_test_files" / "norovirus_v2"
    base = {column: "" for column in NOROVIRUS_V2_METADATA_COLUMNS}
    base.update({
        "LAB_SEQUENCE_ID": "DUMMY_V2_ILLUMINA_001",
        "SPECIES": "Norovirus",
        "ISOLATE": "Synthetic frontend test",
        "SUBTYPE": "GII",
        "DATE_OF_SAMPLING": "01/10/2026",
        "ISOLATION_SOURCE": "Stool",
        "Storage Duration": "< 1 week",
        "Country": "Germany",
        "DATE_OF_RECEIVING": "2026-10-02",
        "PRIME_DIAGNOSTIC_LAB.NAME": "Fictional Diagnostic Lab",
        "PRIME_DIAGNOSTIC_LAB.EMAIL": "diagnostics@example.com",
        "PRIME_DIAGNOSTIC_LAB.ADDRESS": "Example Street 1",
        "PRIME_DIAGNOSTIC_LAB.CITY": "Dresden",
        "PRIME_DIAGNOSTIC_LAB.POSTAL_CODE": "01067",
        "PRIME_DIAGNOSTIC_LAB.COUNTRY": "Germany",
        "HOST_SEX": "Unknown",
        "HOST_BIRTH_MONTH": "01",
        "HOST_BIRTH_YEAR": "1990",
        "Age Group": "35-59",
        "GEOGRAPHIC_LOCATION": "001",
        "Patient Status": "Outpatient",
        "Suspected outbreak": "No",
        "SEQUENCING_REASON": "Synthetic manual testing",
        "DATE_OF_SEQUENCING": "2026-10-03",
        "SEQUENCING_LAB.NAME": "Fictional Sequencing Lab",
        "SEQUENCING_LAB.EMAIL": "sequencing@example.com",
        "SEQUENCING_LAB.ADDRESS": "Example Street 2",
        "SEQUENCING_LAB.CITY": "Dresden",
        "SEQUENCING_LAB.POSTAL_CODE": "01067",
        "SEQUENCING_LAB.COUNTRY": "Germany",
        "SEQUENCING_PLATFORM": "Illumina",
        "SEQUENCING_INSTRUMENT": "MiSeq",
        "ADAPTER": "Synthetic test adapter",
        "PRIMER_SCHEME": "Synthetic test scheme",
        "Illumina R1": "dummy_illumina_R1.fastq.gz",
        "Illumina R2": "dummy_illumina_R2.fastq.gz",
        "REPOSITORY_NAME": "Synthetic test repository",
        "REPOSITORY_LINK": "https://example.com/synthetic-test",
        "REPOSITORY_ID": "DUMMY_ONLY_001",
        "UPLOAD_DATE": "2026-10-04",
    })
    illumina = base.copy()
    nanopore = dict(base, LAB_SEQUENCE_ID="DUMMY_V2_NANOPORE_001",
                    SEQUENCING_PLATFORM="Oxford Nanopore",
                    SEQUENCING_INSTRUMENT="MinION",
                    Nanopore="dummy_nanopore.fastq.gz")
    pacbio = dict(base, LAB_SEQUENCE_ID="DUMMY_V2_PACBIO_001",
                  SEQUENCING_PLATFORM="PacBio", SEQUENCING_INSTRUMENT="Sequel II",
                  PacBio="dummy_pacbio.fastq.gz")
    for row in (nanopore, pacbio):
        row["Illumina R1"] = row["Illumina R2"] = ""
    paired = [base["Illumina R1"], base["Illumina R2"]]
    cases = [
        ("01_valid_illumina", [illumina], paired, None),
        ("02_valid_nanopore", [nanopore], [nanopore["Nanopore"]], None),
        ("03_valid_pacbio", [pacbio], [pacbio["PacBio"]], None),
        ("04_valid_bulk", [illumina, nanopore, pacbio],
         paired + [nanopore["Nanopore"], pacbio["PacBio"]], None),
        ("05_invalid_email", [dict(base, **{"SEQUENCING_LAB.EMAIL": "bad-email"})],
         paired, "invalid email"),
        ("06_invalid_location", [dict(base, GEOGRAPHIC_LOCATION="1")],
         paired, "exactly three digits"),
        ("07_missing_read", [illumina], paired[:1], "were not uploaded"),
        ("08_duplicate_ids_bulk", [illumina, illumina.copy()],
         paired, "Duplicate LAB_SEQUENCE_ID"),
        ("09_r2_without_r1", [dict(base, **{"Illumina R1": ""})],
         paired[1:], "Illumina R2 cannot"),
    ]
    for name, rows, filenames, expected_error in cases:
        folder = output / name
        folder.mkdir(parents=True, exist_ok=True)
        metadata = folder / "metadata.csv"
        with metadata.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(base))
            writer.writeheader()
            writer.writerows(rows)
        uploads = []
        for filename in filenames:
            # Artificial repeated bases, not biological sequence data.
            sequence = "ACGT" * 25
            content = f"@SYNTHETIC_TEST_ONLY\n{sequence}\n+\n{'I' * len(sequence)}\n"
            compressed = gzip.compress(content.encode(), mtime=0)
            (folder / filename).write_bytes(compressed)
            uploads.append(SimpleUploadedFile(filename, compressed))
        try:
            result = validate_upload(
                metadata_file=SimpleUploadedFile("metadata.csv", metadata.read_bytes()),
                fastq_files=uploads,
                max_rows=None if "bulk" in name else 1,
            )
        except ValueError as exc:
            if expected_error is None or expected_error not in str(exc):
                raise
        else:
            if expected_error:
                raise AssertionError(f"{name} unexpectedly passed")
            assert result["metadata_df"].iloc[0]["geographic_location"] == "001"
            assert result["metadata_df"].iloc[0]["prime_diagnostic_lab.postal_code"] == "01067"
        print(f"Verified {name}")


if __name__ == "__main__":
    main()
