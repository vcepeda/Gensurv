from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gensurvapp", "0031_submission_submission_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysisresult",
            name="submission",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="analysis_results",
                to="gensurvapp.submission",
            ),
        ),
        migrations.AddConstraint(
            model_name="analysisresult",
            constraint=models.UniqueConstraint(
                condition=models.Q(("submission__isnull", False)),
                fields=("submission", "sample_id"),
                name="uniq_analysisresult_submission_sample",
            ),
        ),
        migrations.AddIndex(
            model_name="analysisresult",
            index=models.Index(fields=["submission", "sample_id"], name="gapp_anres_sub_samp_idx"),
        ),
    ]
