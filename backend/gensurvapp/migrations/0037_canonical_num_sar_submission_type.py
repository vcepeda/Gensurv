from django.db import migrations, models


def canonicalize_submissions(apps, schema_editor):
    Submission = apps.get_model("gensurvapp", "Submission")
    Submission.objects.using(schema_editor.connection.alias).filter(
        submission_type="norovirus_v2"
    ).update(submission_type="num-sar_norovirus")


class Migration(migrations.Migration):
    dependencies = [("gensurvapp", "0036_preserve_norovirus_v2_submission_type")]

    operations = [
        # Intentionally irreversible: the canonical value cannot tell us which
        # records used the old identifier. Restore a backup to undo the rename.
        migrations.RunPython(canonicalize_submissions),
        migrations.AlterField(
            model_name="submission",
            name="submission_type",
            field=models.CharField(
                max_length=20,
                default="gensurv",
                choices=[
                    ("num-sar_norovirus", "NUM-SAR/Norovirus"),
                    ("cogdat", "COGDAT"),
                    ("gensurv", "Gensurv"),
                ],
            ),
        ),
    ]
