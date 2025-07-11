# Generated by Django 4.2.14 on 2024-10-22 09:31

from django.db import migrations, models
import gensurvapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0009_remove_submission_fastq_files'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='antibiotics_file',
            field=models.FileField(blank=True, null=True, upload_to=gensurvapp.models.user_submission_path),
        ),
        migrations.AlterField(
            model_name='submission',
            name='metadata_file',
            field=models.FileField(upload_to=gensurvapp.models.user_submission_path),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(upload_to=gensurvapp.models.user_submission_path),
        ),
    ]
