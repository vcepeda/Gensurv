from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gensurvapp", "0033_submission_metadata_statistics"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalStatistics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("singleton_key", models.PositiveSmallIntegerField(default=1, unique=True)),
                ("stats_version", models.PositiveIntegerField(default=1)),
                ("total_submissions", models.PositiveIntegerField(default=0)),
                ("total_metadata_rows", models.PositiveIntegerField(default=0)),
                ("total_fastq_files", models.PositiveIntegerField(default=0)),
                ("total_antibiotics_files", models.PositiveIntegerField(default=0)),
                ("total_unique_sample_identifiers", models.PositiveIntegerField(default=0)),
                ("total_unique_isolate_species", models.PositiveIntegerField(default=0)),
                ("platform_counts", models.JSONField(blank=True, default=dict)),
                ("sir_counts", models.JSONField(blank=True, default=dict)),
                ("mic_numeric_values", models.JSONField(blank=True, default=list)),
                ("map_location_counts", models.JSONField(blank=True, default=list)),
                ("last_recomputed_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
