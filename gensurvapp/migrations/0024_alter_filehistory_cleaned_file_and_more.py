# Generated by Django 4.2.14 on 2025-06-13 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0023_filehistory_cleaned_file_alter_filehistory_file_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filehistory',
            name='cleaned_file',
            field=models.FileField(blank=True, max_length=500, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='filehistory',
            name='file_type',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='filehistory',
            name='old_file',
            field=models.FileField(max_length=500, upload_to=''),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='file_type',
            field=models.CharField(max_length=30),
        ),
    ]
