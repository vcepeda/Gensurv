# Generated by Django 4.2.14 on 2024-11-13 11:20

from django.db import migrations, models
import gensurvapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0012_remove_submission_antibiotics_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='antibiotics_file',
            field=models.FileField(blank=True, max_length=255, null=True, upload_to=gensurvapp.models.user_submission_path),
        ),
        migrations.AddField(
            model_name='submission',
            name='metadata_file',
            field=models.FileField(default='', max_length=255, upload_to=gensurvapp.models.user_submission_path),
            preserve_default=False,
        ),
    ]
