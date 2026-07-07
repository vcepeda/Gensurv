from __future__ import annotations

import argparse
import os
from pathlib import Path


def setup_django() -> None:
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gensurv_project.settings")

	import django

	django.setup()


def iter_result_directories(all_results_dir: Path):
	for entry in sorted(all_results_dir.iterdir(), key=lambda p: p.name.lower()):
		if entry.is_dir():
			yield entry


def fill_analysis_results(all_results_dir: Path, dry_run: bool = False) -> None:
	from gensurvapp.models import AnalysisResult

	created = 0
	updated = 0
	skipped = 0

	if not all_results_dir.exists() or not all_results_dir.is_dir():
		raise FileNotFoundError(f"Directory not found: {all_results_dir}")

	for result_dir in iter_result_directories(all_results_dir):
		sample_id = result_dir.name
		result_path = str(result_dir.resolve())

		existing_qs = AnalysisResult.objects.filter(submission__isnull=True, sample_id=sample_id)
		existing_count = existing_qs.count()

		if existing_count == 0:
			if not dry_run:
				AnalysisResult.objects.create(
					submission=None,
					sample_id=sample_id,
					result_directory=result_path,
					status="finished",
				)
			created += 1
			continue

		if not dry_run:
			existing_qs.update(result_directory=result_path, status="finished")

		if existing_count == 1:
			updated += 1
		else:
			skipped += 1
			print(
				f"Warning: found {existing_count} rows for sample_id='{sample_id}' with submission=None; "
				"updated all matching rows."
			)

	mode = "DRY RUN" if dry_run else "APPLIED"
	print(f"Done ({mode}). created={created}, updated={updated}, warnings={skipped}")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Fill AnalysisResult from runs/all_results")
	parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to the database")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	all_results_dir = Path(__file__).resolve().parents[1] / "runs" / "all_results"
	setup_django()
	fill_analysis_results(all_results_dir, dry_run=args.dry_run)


if __name__ == "__main__":
	main()