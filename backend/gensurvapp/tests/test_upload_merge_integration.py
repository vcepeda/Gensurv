"""Regression coverage for the main/V2 upload integration."""
import csv
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from gensurvapp.models import Submission, UploadedFile, FileHistory, AnalysisResult
from gensurvapp.norovirus_v2_constants import NOROVIRUS_V2_METADATA_COLUMNS
from gensurvapp.services import upload_service


class UploadMergeIntegrationTests(TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="gensurv-upload-test-")
        self.addCleanup(temp.cleanup)
        override = override_settings(MEDIA_ROOT=temp.name, ALLOWED_HOSTS=["testserver"])
        override.enable()
        self.addCleanup(override.disable)
        self.media = Path(temp.name)
        self.user = get_user_model().objects.create_user(username="fixture-user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        notifier = patch("gensurvapp.views.notify_admin_of_upload")
        notifier.start()
        self.addCleanup(notifier.stop)

    def row(self, sample="TEST_1"):
        row = {name: ("Synthetic" if required else "")
               for name, (_, required) in NOROVIRUS_V2_METADATA_COLUMNS.items()}
        row.update({
            "LAB_SEQUENCE_ID": sample, "SPECIES": "Norovirus",
            "DATE_OF_RECEIVING": "2026-10-01", "DATE_OF_SEQUENCING": "2026-10-02",
            "DATE_OF_SAMPLING": "01/10/2026", "GEOGRAPHIC_LOCATION": "001",
            "PRIME_DIAGNOSTIC_LAB.EMAIL": "lab@example.com",
            "SEQUENCING_LAB.EMAIL": "seq@example.com",
            "PRIME_DIAGNOSTIC_LAB.POSTAL_CODE": "01067",
            "SEQUENCING_PLATFORM": "Illumina", "HOST_SEX": "Unknown",
            "Illumina R1": f"{sample}_R1.fastq", "Illumina R2": f"{sample}_R2.fastq",
        })
        return row

    def metadata(self, rows):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(NOROVIRUS_V2_METADATA_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
        return SimpleUploadedFile("metadata.csv", stream.getvalue().encode())

    def upload(self, rows, bulk=False, dry=False):
        names = {row[col] for row in rows for col in ("Illumina R1", "Illumina R2", "Nanopore", "PacBio") if row[col]}
        files = [SimpleUploadedFile(name, b"@synthetic\nACGT\n+\nIIII\n") for name in sorted(names)]
        return self.client.post(
            f'/api/upload/{"bulk" if bulk else "single"}/?type=num-sar_norovirus&dry_run={str(dry).lower()}',
            {"metadata_file": self.metadata(rows), "fastq_files": files, "submit_to_pipeline": "false"},
            format="multipart",
        )

    def test_single_dry_run_and_invalid_inputs_do_not_persist(self):
        response = self.upload([self.row()], dry=True)
        self.assertEqual(response.status_code, 200, response.data)
        row = self.row()
        row["SEQUENCING_LAB.EMAIL"] = "bad-email"
        self.assertEqual(self.upload([row]).status_code, 400)
        self.assertEqual(self.upload([self.row(), self.row()], bulk=True).status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(UploadedFile.objects.count(), 0)
        self.assertEqual(list(self.media.rglob("*.csv")), [])

    def test_single_bulk_persistence_and_dashboard_files(self):
        for bulk in (False, True):
            with self.subTest(bulk=bulk):
                rows = [self.row("A")]
                if bulk:
                    row = self.row("B")
                    row.update({"Illumina R1": "", "Illumina R2": "", "Nanopore": "B.fastq", "SEQUENCING_PLATFORM": "Nanopore"})
                    rows.append(row)
                response = self.upload(rows, bulk=bulk)
                self.assertEqual(response.status_code, 201, response.data)
                submission = Submission.objects.get(pk=response.data["submission_id"])
                self.assertEqual(submission.submission_type, "num-sar_norovirus")
                self.assertEqual(submission.is_bulk_upload, bulk)
                self.assertEqual(AnalysisResult.objects.filter(submission=submission).count(), len(rows))
                raw = submission.files.get(file_type="metadata_raw")
                with raw.file.open("rb") as stream:
                    self.assertIn(b"LAB_SEQUENCE_ID", stream.read())
                with raw.cleaned_file.open("rb") as stream:
                    cleaned = stream.read()
                    self.assertIn(b"01067", cleaned)
                    self.assertIn(b"001", cleaned)
                self.assertFalse(submission.files.filter(file_type="metadata_converted").exists())
        dashboard = self.client.get("/api/dashboard/")
        self.assertEqual(dashboard.status_code, 200, dashboard.data)
        self.assertIn("cleaned_url", str(dashboard.data))
        self.assertIn("raw_url", str(dashboard.data))

    def test_resubmission_preserves_history_for_both_type_identifiers(self):
        for kind in ("num-sar_norovirus", "norovirus_v2"):
            with self.subTest(kind=kind):
                response = self.upload([self.row()])
                self.assertEqual(response.status_code, 201, response.data)
                submission = Submission.objects.get(pk=response.data["submission_id"])
                submission.submission_type = kind
                submission.resubmission_allowed = True
                submission.save()
                url = f"/api/submissions/{submission.pk}/resubmissions/metadata/"
                invalid = self.row()
                invalid["GEOGRAPHIC_LOCATION"] = "1"
                self.assertEqual(self.client.post(url, {"file": self.metadata([invalid])}, format="multipart").status_code, 400)
                self.assertFalse(FileHistory.objects.filter(submission=submission).exists())
                updated = self.row()
                updated["ISOLATE"] = "Replacement"
                result = self.client.post(url, {"file": self.metadata([updated])}, format="multipart")
                self.assertEqual(result.status_code, 200, result.data)
                history = FileHistory.objects.get(submission=submission)
                self.assertTrue(history.old_file.storage.exists(history.old_file.name))
                self.assertTrue(history.cleaned_file.storage.exists(history.cleaned_file.name))
                raw = submission.files.get(file_type="metadata_raw")
                with raw.file.open("rb") as stream:
                    self.assertIn(b"Replacement", stream.read())

    def test_gensurv_antibiotics_optional_and_validated(self):
        # Isolate antibiotic branching from unrelated taxonomy/schema validation.
        for bulk in (False, True):
            for mode in ("none", "info", "file", "missing", "invalid"):
                with self.subTest(bulk=bulk, mode=mode):
                    frame = pd.DataFrame([{
                        "sample identifier": "TEST", "illumina r1": "test.fastq",
                        "antibiotics file": "ab.csv" if mode in {"file", "missing", "invalid"} else "",
                        "antibiotics info": "Not tested" if mode == "info" else "",
                    }])
                    results = [(True, False, "", ",", frame)]
                    if mode in {"file", "invalid"}:
                        results.append((mode != "invalid", False, "invalid antibiotic data", ",", pd.DataFrame([{"antibiotic": "test"}])))
                    kwargs = dict(user=self.user, metadata_file=SimpleUploadedFile("metadata.csv", b"test"), fastq_files=[SimpleUploadedFile("test.fastq", b"test")], submission_type="gensurv", dry_run=True)
                    antibiotic = SimpleUploadedFile("ab.csv", b"test") if mode in {"file", "invalid"} else None
                    if bulk:
                        kwargs["antibiotics_files"] = [antibiotic] if antibiotic else []
                        handler = upload_service.handle_bulk_upload
                    else:
                        kwargs["uploaded_antibiotics_file"] = antibiotic
                        handler = upload_service.handle_single_upload
                    with patch.object(upload_service, "validate_and_save_csv", side_effect=results):
                        if mode in {"missing", "invalid"}:
                            with self.assertRaises(ValueError):
                                handler(**kwargs)
                        else:
                            self.assertTrue(handler(**kwargs)["dry_run"])
