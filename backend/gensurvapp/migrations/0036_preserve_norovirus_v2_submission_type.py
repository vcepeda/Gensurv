from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("gensurvapp", "0035_alter_submission_submission_type")]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="submission_type",
            field=models.CharField(
                max_length=20,
                default="gensurv",
                choices=[
                    ("num-sar_norovirus", "NUM-SAR/Norovirus"),
                    ("norovirus_v2", "NUM-SAR/Norovirus (legacy V2 identifier)"),
                    ("cogdat", "COGDAT"),
                    ("gensurv", "Gensurv"),
                ],
            ),
        ),
    ]
