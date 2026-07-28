import os

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gensurvapp.models import AnalysisResult


class Command(BaseCommand):
    help = (
        "After a Bactopia batch run finishes, links its per-sample output "
        "folders to the matching AnalysisResult row(s) so the app picks them "
        "up (Dashboard/Results tab, per-submission results dashboard). Each "
        "immediate subdirectory of <batch_dir> is treated as one sample's "
        "output, named by sample_id (e.g. runs/pacbio_batch/NRZ84964RV/), and "
        "sets result_directory + status='finished' on the matching row. "
        "sample_id is only unique per-submission by design (the same sample "
        "can legitimately be re-run independently under different "
        "submissions), so if a sample_id matches more than one submission "
        "and --submission-id wasn't given to disambiguate, that sample is "
        "skipped and reported rather than guessed at - it never links (or "
        "silently overwrites) more than one submission's row per run. "
        "Dry-run by default."
    )

    def add_arguments(self, parser):
        parser.add_argument("batch_dir", type=str, help="Path to the completed Bactopia run's output directory, e.g. /mnt/storage/ahcepev1/Bactopia-runs/runs/pacbio_batch")
        parser.add_argument("--submission-id", type=int, default=None, help="Only link samples belonging to this submission (default: link for any submission with a matching sample_id)")
        parser.add_argument("--apply", action="store_true", help="Actually update the database. Without this, only reports what would happen.")

    def handle(self, *args, **options):
        batch_dir = options["batch_dir"]
        submission_id = options["submission_id"]
        apply_changes = options["apply"]

        if not os.path.isdir(batch_dir):
            raise CommandError(f"Not a directory: {batch_dir}")

        sample_dirs = sorted(
            entry for entry in os.listdir(batch_dir)
            if os.path.isdir(os.path.join(batch_dir, entry))
        )
        if not sample_dirs:
            self.stdout.write(self.style.WARNING(f"No subdirectories found under {batch_dir} - nothing to link."))
            return

        linked = 0
        unmatched = []
        ambiguous = []

        for sample_id in sample_dirs:
            result_path = os.path.abspath(os.path.join(batch_dir, sample_id))

            qs = AnalysisResult.objects.filter(sample_id=sample_id)
            if submission_id is not None:
                qs = qs.filter(submission_id=submission_id)

            rows = list(qs)
            if not rows:
                # If --submission-id was given, check whether this sample_id
                # exists at all under a *different* submission, so the report
                # doesn't wrongly claim it was "never uploaded" when it's
                # really just linked to a submission other than the one asked for.
                if submission_id is not None and AnalysisResult.objects.filter(sample_id=sample_id).exists():
                    other_ids = sorted(set(
                        AnalysisResult.objects.filter(sample_id=sample_id).values_list("submission_id", flat=True)
                    ), key=lambda x: (x is None, x))
                    self.stderr.write(self.style.ERROR(
                        f"  [NOT IN THIS SUBMISSION] sample_id={sample_id} exists under submission(s) "
                        f"{other_ids}, not submission {submission_id} - skipped."
                    ))
                else:
                    unmatched.append(sample_id)
                continue

            distinct_submissions = {row.submission_id for row in rows}
            if submission_id is None and len(distinct_submissions) > 1:
                ambiguous.append((sample_id, sorted(distinct_submissions, key=lambda x: (x is None, x))))
                self.stderr.write(self.style.ERROR(
                    f"  [AMBIGUOUS] sample_id={sample_id} matches {len(distinct_submissions)} different "
                    f"submissions ({', '.join(str(s) for s in sorted(distinct_submissions, key=lambda x: (x is None, x)))}) "
                    f"- skipped. Re-run with --submission-id to pick which one this batch belongs to."
                ))
                continue

            for row in rows:
                already_linked = row.status == "finished" and row.result_directory == result_path
                marker = "already linked" if already_linked else "WILL LINK"
                self.stdout.write(
                    f"  [{marker}] sample_id={sample_id} submission_id={row.submission_id} "
                    f"-> {result_path}"
                )
                if already_linked:
                    continue

                linked += 1
                if apply_changes:
                    row.result_directory = result_path
                    row.status = "finished"
                    row.completion_date = timezone.now()
                    row.save(update_fields=["result_directory", "status", "completion_date"])

        self.stdout.write("")
        if ambiguous:
            self.stdout.write(self.style.ERROR(
                f"{len(ambiguous)} sample(s) skipped as ambiguous (matched multiple submissions, "
                f"no --submission-id given): {', '.join(s for s, _ in ambiguous)}"
            ))
        if unmatched:
            self.stdout.write(self.style.WARNING(
                f"{len(unmatched)} sample folder(s) in {batch_dir} have no matching AnalysisResult row "
                f"(never uploaded/tracked by the app, or sample_id mismatch): {', '.join(unmatched)}"
            ))

        if not apply_changes:
            self.stdout.write(self.style.WARNING(
                f"Dry run - {linked} row(s) would be linked. Re-run with --apply to write changes."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"Linked {linked} sample(s) to their Bactopia results."))
