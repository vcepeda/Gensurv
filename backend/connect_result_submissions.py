#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def setup_django() -> None:
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gensurv_project.settings")

	import django

	django.setup()


def _clean_sample_ids(series) -> list[str]:
	cleaned = []
	seen = set()
	for value in series.astype(str).str.strip().tolist():
		if not value or value.lower() == "nan":
			continue
		if value not in seen:
			seen.add(value)
			cleaned.append(value)
	return cleaned


def _read_metadata_sample_ids(file_path: str) -> list[str]:
	# sep=None lets pandas sniff comma/semicolon/tab delimiters used in uploads.
	df = pd.read_csv(file_path, sep=None, engine="python", dtype=str)
	df.columns = df.columns.str.strip().str.lower()

	if "sample identifier" not in df.columns:
		return []

	return _clean_sample_ids(df["sample identifier"])


def connect_results_to_submissions() -> None:
	from gensurvapp.models import AnalysisResult, Submission, UploadedFile

	submissions_total = 0
	submissions_with_metadata = 0
	links_created = 0
	missing_result_count = 0
	conflict_count = 0
	duplicate_or_ambiguous_count = 0
	metadata_parse_errors = 0

	for submission in Submission.objects.all().order_by("id"):
		submissions_total += 1

		metadata_file = (
			UploadedFile.objects.filter(
				submission=submission,
				file_type__in=["metadata_raw", "metadata_cleaned"],
			)
			.exclude(cleaned_file="")
			.order_by("-id")
			.first()
		)

		if not metadata_file:
			metadata_file = (
				UploadedFile.objects.filter(
					submission=submission,
					file_type__in=["metadata_raw", "metadata_cleaned"],
				)
				.order_by("-id")
				.first()
			)

		if not metadata_file:
			continue

		submissions_with_metadata += 1

		path_candidates = []
		if metadata_file.cleaned_file:
			try:
				path_candidates.append(metadata_file.cleaned_file.path)
			except Exception:
				pass
		if metadata_file.file:
			try:
				path_candidates.append(metadata_file.file.path)
			except Exception:
				pass

		sample_ids = []
		for path in path_candidates:
			try:
				sample_ids = _read_metadata_sample_ids(path)
				if sample_ids:
					break
			except Exception:
				continue

		if not sample_ids:
			metadata_parse_errors += 1
			print(f"Submission {submission.id}: unable to read sample identifiers from metadata.")
			continue

		for sample_id in sample_ids:
			# Skip if already connected for this submission/sample pair.
			if AnalysisResult.objects.filter(submission=submission, sample_id=sample_id).exists():
				continue

			exact_qs = AnalysisResult.objects.filter(submission__isnull=True, sample_id=sample_id).order_by("id")
			exact_count = exact_qs.count()

			target = None
			if exact_count == 1:
				target = exact_qs.first()
			elif exact_count > 1:
				duplicate_or_ambiguous_count += 1
				print(
					f"Submission {submission.id}, sample '{sample_id}': "
					f"multiple unlinked AnalysisResult rows found (exact match)."
				)
				continue
			else:
				ci_qs = AnalysisResult.objects.filter(
					submission__isnull=True,
					sample_id__iexact=sample_id,
				).order_by("id")
				ci_count = ci_qs.count()
				if ci_count == 1:
					target = ci_qs.first()
				elif ci_count > 1:
					duplicate_or_ambiguous_count += 1
					print(
						f"Submission {submission.id}, sample '{sample_id}': "
						f"multiple unlinked AnalysisResult rows found (case-insensitive match)."
					)
					continue
				else:
					missing_result_count += 1
					print(f"Submission {submission.id}, sample '{sample_id}': no unlinked AnalysisResult found.")
					continue

			if AnalysisResult.objects.filter(submission=submission, sample_id=target.sample_id).exists():
				conflict_count += 1
				print(
					f"Submission {submission.id}, sample '{sample_id}': "
					"link conflict, submission already has this sample_id."
				)
				continue

			target.submission = submission
			target.save(update_fields=["submission"])
			links_created += 1

	print("Done.")
	print(f"Submissions scanned: {submissions_total}")
	print(f"Submissions with metadata: {submissions_with_metadata}")
	print(f"Links created: {links_created}")
	print(f"Missing results: {missing_result_count}")
	print(f"Conflicts: {conflict_count}")
	print(f"Ambiguous duplicates: {duplicate_or_ambiguous_count}")
	print(f"Metadata parse failures: {metadata_parse_errors}")


def main() -> None:
	setup_django()
	connect_results_to_submissions()


if __name__ == "__main__":
	main()
