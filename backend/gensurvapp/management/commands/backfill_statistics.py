import os
import pandas as pd
from django.core.management.base import BaseCommand
from gensurvapp.models import Submission
from gensurvapp.services.upload_service import generate_statistics
from gensurvapp.services.global_stats_service import recompute_global_statistics


def read_df(file_field):
    if not file_field:
        return None
    path = getattr(file_field, 'path', None)
    if not path or not os.path.exists(path):
        return None
    try:
        ext = os.path.splitext(path.lower())[1]
        if ext == '.xlsx':
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path, sep=None, engine='python')
        if df is not None and not df.empty:
            df.columns = df.columns.str.lower().str.strip()
            return df
    except Exception as e:
        print(f"  Could not read {path}: {e}")
    return None


class Command(BaseCommand):
    help = 'Backfill metadata_statistics for existing submissions'

    def handle(self, *args, **kwargs):
        submissions = Submission.objects.filter(metadata_statistics={})
        total = submissions.count()
        self.stdout.write(f"Found {total} submissions with empty statistics")

        updated = 0
        for submission in submissions:
            # get metadata file
            meta_file = submission.files.filter(
                file_type__in=['metadata_cleaned', 'metadata_raw']
            ).order_by('id').first()

            if not meta_file:
                self.stdout.write(f"  Submission {submission.id}: no metadata file, skipping")
                continue

            candidate = meta_file.cleaned_file if meta_file.cleaned_file else meta_file.file
            metadata_df = read_df(candidate)

            if metadata_df is None:
                self.stdout.write(f"  Submission {submission.id}: could not read metadata file, skipping")
                continue

            # get antibiotics files
            ab_files = submission.files.filter(file_type='antibiotics_raw')
            antibiotics_dfs = []
            for ab in ab_files:
                ab_df = read_df(ab.cleaned_file if ab.cleaned_file else ab.file)
                if ab_df is not None:
                    antibiotics_dfs.append(ab_df)

            stats = generate_statistics(
                metadata_df,
                submission.submission_type or 'bacteria',
                antibiotics_dfs,
            )
            submission.metadata_statistics = stats
            submission.save(update_fields=['metadata_statistics'])
            updated += 1
            self.stdout.write(f"  Submission {submission.id}: updated")

        self.stdout.write(f"\nUpdated {updated}/{total} submissions")
        self.stdout.write("Recomputing global statistics...")
        recompute_global_statistics()
        self.stdout.write("Done!")
