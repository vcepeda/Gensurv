from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gensurvapp", "0032_analysisresult_submission_scope"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="metadata_statistics",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
    