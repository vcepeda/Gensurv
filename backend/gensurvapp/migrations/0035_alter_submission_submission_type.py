# Generated manually for the Norovirus V2 submission type.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gensurvapp", "0034_globalstatistics_qc_rank_counts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="submission_type",
            field=models.CharField(
                choices=[
                    ("num-sar_bacteria", "NUM-SAR/Bacteria"),
                    ("num-sar_virus", "NUM-SAR/Virus"),
                    ("norovirus_v2", "Norovirus V2"),
                    ("cogdat", "COGDAT"),
                    ("gensurv", "Gensurv"),
                ],
                default="gensurv",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="uploadedfile",
            name="file_type",
            field=models.CharField(
                choices=[
                    ("metadata_raw", "Metadata Raw"),
                    ("metadata_cleaned", "Metadata Cleaned"),
                    ("metadata_converted", "Converted NUM-SAR Metadata"),
                    ("antibiotics_raw", "Antibiotics Raw"),
                    ("antibiotics_cleaned", "Antibiotics Cleaned"),
                    ("fastq", "FASTQ"),
                ],
                max_length=30,
            ),
        ),
    ]
