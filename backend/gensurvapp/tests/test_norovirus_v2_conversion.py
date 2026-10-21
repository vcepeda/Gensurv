import unittest

import pandas as pd

from gensurvapp.services.norovirus_v2_conversion import (
    add_num_sar_file_columns,
    map_sequencing_files_to_num_sar,
)


class NorovirusV2SequencingFileConversionTests(unittest.TestCase):
    def test_maps_paired_illumina_files(self):
        result = map_sequencing_files_to_num_sar(
            {
                "illumina r1": "sample_R1.fastq.gz",
                "illumina r2": "sample_R2.fastq.gz",
            }
        )

        self.assertEqual(result["FILE_1_NAME"], "sample_R1.fastq.gz")
        self.assertEqual(result["FILE_2_NAME"], "sample_R2.fastq.gz")

    def test_maps_single_end_illumina_file(self):
        result = map_sequencing_files_to_num_sar(
            {"illumina r1": "sample_R1.fastq.gz"}
        )

        self.assertEqual(result["FILE_1_NAME"], "sample_R1.fastq.gz")
        self.assertIsNone(result["FILE_2_NAME"])

    def test_maps_nanopore_file(self):
        result = map_sequencing_files_to_num_sar(
            {"nanopore": "sample_nanopore.fastq.gz"}
        )

        self.assertEqual(result["FILE_1_NAME"], "sample_nanopore.fastq.gz")
        self.assertIsNone(result["FILE_2_NAME"])

    def test_maps_pacbio_file(self):
        result = map_sequencing_files_to_num_sar(
            {"pacbio": "sample_pacbio.fastq.gz"}
        )

        self.assertEqual(result["FILE_1_NAME"], "sample_pacbio.fastq.gz")
        self.assertIsNone(result["FILE_2_NAME"])

    def test_rejects_r2_without_r1(self):
        with self.assertRaisesRegex(ValueError, "R2 cannot be provided"):
            map_sequencing_files_to_num_sar(
                {"illumina r2": "sample_R2.fastq.gz"}
            )

    def test_rejects_multiple_platform_families(self):
        with self.assertRaisesRegex(ValueError, "multiple sequencing platform"):
            map_sequencing_files_to_num_sar(
                {
                    "illumina r1": "sample_R1.fastq.gz",
                    "nanopore": "sample_nanopore.fastq.gz",
                }
            )

    def test_adds_file_columns_without_modifying_input(self):
        source_df = pd.DataFrame(
            [{"lab_sequence_id": "sample-1", "pacbio": "sample.bam"}]
        )

        result = add_num_sar_file_columns(source_df)

        self.assertNotIn("FILE_1_NAME", source_df.columns)
        self.assertEqual(result.loc[0, "FILE_1_NAME"], "sample.bam")
        self.assertIsNone(result.loc[0, "FILE_2_NAME"])


if __name__ == "__main__":
    unittest.main()
