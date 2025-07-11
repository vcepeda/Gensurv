# Generated by Django 4.2.14 on 2024-11-24 20:22

from django.db import migrations, models
import django.db.models.deletion
import gensurvapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0013_submission_antibiotics_file_submission_metadata_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='antibiotics_file',
        ),
        migrations.AddField(
            model_name='submission',
            name='is_bulk_upload',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uploadedfile',
            name='sample_id',
            field=models.CharField(default='default_sample_id', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(upload_to='uploaded_files/'),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='file_type',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gensurvapp.submission'),
        ),
        migrations.CreateModel(
            name='SampleFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sample_id', models.CharField(max_length=100)),
                ('file_type', models.CharField(choices=[('metadata', 'Metadata'), ('antibiotics', 'Antibiotics'), ('fastq', 'FASTQ')], max_length=20)),
                ('file', models.FileField(upload_to=gensurvapp.models.user_submission_path)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sample_files', to='gensurvapp.submission')),
            ],
        ),
    ]
