# Generated manually to align submission_type choices with upload type handling.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gensurvapp", "0034_globalstatistics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="submission_type",
            field=models.CharField(
                choices=[
                    ("num-sar_bacteria", "NUM-SAR/Bacteria"),
                    ("num-sar_virus", "NUM-SAR/Virus"),
                    ("cogdat", "COGDAT"),
                    ("gensurv", "Gensurv"),
                ],
                default="gensurv",
                max_length=20,
            ),
        ),
    ]

