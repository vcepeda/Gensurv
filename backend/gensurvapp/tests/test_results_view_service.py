import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gensurvapp.services.results_view_service import build_sample_analyses


class ResultsViewServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        gtdbtk = self.root / "tools" / "gtdbtk"
        gtdbtk.mkdir(parents=True)
        (gtdbtk / "sample.one.tsv").write_text(
            "classification\n"
            "d__Bacteria;g__Escherichia;s__Escherichia coli_C\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_species_filter_and_exact_sample_name(self):
        ectyper = self.root / "tools" / "ectyper"
        ectyper.mkdir()
        with (ectyper / "sample.one.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["Serotype"])
            writer.writerow(["O9:H10"])
        config = [{
            "key": "ectyper", "folder": "tools/ectyper", "title": "E. coli serotype",
            "file": "{sample}.tsv", "header": True, "columns": ["Serotype"],
            "applies_to": {"genera": ["Escherichia"]},
        }]
        with patch("gensurvapp.services.results_view_service.load_results_view_config", return_value=config):
            payload = build_sample_analyses(self.root, "sample.one")
        self.assertEqual(payload["species"], "Escherichia coli")
        self.assertEqual(payload["analyses"][0]["rows"], [["O9:H10"]])

    def test_headerless_file_keeps_first_row(self):
        mlst = self.root / "tools" / "mlst"
        mlst.mkdir()
        (mlst / "sample.one.tsv").write_text("sample.one.fna\tecoli\t10\n", encoding="utf-8")
        config = [{
            "key": "mlst", "folder": "tools/mlst", "title": "MLST",
            "file": "{sample}.tsv", "header": False,
            "columns": ["File", "Scheme", "ST"], "use_columns": [0, 1, 2],
        }]
        with patch("gensurvapp.services.results_view_service.load_results_view_config", return_value=config):
            analysis = build_sample_analyses(self.root, "sample.one")["analyses"][0]
        self.assertEqual(analysis["rows"], [["sample.one.fna", "ecoli", "10"]])

    def test_empty_file_is_not_run(self):
        pling = self.root / "tools" / "pling"
        pling.mkdir()
        (pling / "sample.one.tsv").touch()
        config = [{
            "key": "pling", "folder": "tools/pling", "title": "Plasmid types",
            "file": "{sample}.tsv", "header": True, "columns": ["plasmid", "type"],
        }]
        with patch("gensurvapp.services.results_view_service.load_results_view_config", return_value=config):
            analysis = build_sample_analyses(self.root, "sample.one")["analyses"][0]
        self.assertEqual(analysis["status"], "not_run")


if __name__ == "__main__":
    unittest.main()
