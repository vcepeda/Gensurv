#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def setup_django() -> None:
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gensurv_project.settings")

	import django

	django.setup()


def _read_sample_identifiers(metadata_path: str) -> list[str]:
	df = pd.read_csv(metadata_path, sep=None, engine="python", dtype=str)
	df.columns = df.columns.str.strip().str.lower()

	if "sample identifier" not in df.columns:
		return []

	sample_ids: list[str] = []
	seen: set[str] = set()
	for value in df["sample identifier"].astype(str).str.strip().tolist():
		if not value or value.lower() == "nan":
			continue
		if value in seen:
			continue
		sample_ids.append(value)
		seen.add(value)
	return sample_ids


def _get_submission_metadata_path(submission) -> str | None:
	from gensurvapp.models import UploadedFile

	metadata_upload = (
		UploadedFile.objects.filter(
			submission=submission,
			file_type__in=["metadata_raw", "metadata_cleaned"],
		)
		.order_by("-id")
		.first()
	)
	if not metadata_upload:
		return None

	if metadata_upload.cleaned_file:
		try:
			return metadata_upload.cleaned_file.path
		except Exception:
			pass

	if metadata_upload.file:
		try:
			return metadata_upload.file.path
		except Exception:
			pass

	return None


def _build_result_dir_map(all_results_dir: Path) -> dict[str, str]:
	if not all_results_dir.exists() or not all_results_dir.is_dir():
		raise FileNotFoundError(f"Directory not found: {all_results_dir}")

	result_map: dict[str, str] = {}
	for child in all_results_dir.iterdir():
		if not child.is_dir():
			continue

		key = child.name.lower()
		if key not in result_map:
			result_map[key] = str(child.resolve())
	return result_map


def run() -> None:
	from gensurvapp.models import AnalysisResult, Submission

	all_results_dir = Path(__file__).resolve().parents[1] / "runs" / "all_results"
	result_dir_map = _build_result_dir_map(all_results_dir)

	for submission in Submission.objects.all().order_by("id"):
		metadata_path = _get_submission_metadata_path(submission)
		if not metadata_path:
			continue

		try:
			sample_ids = _read_sample_identifiers(metadata_path)
		except Exception as exc:
			print(f"Submission {submission.id}: failed to parse metadata ({exc}).")
			continue

		for sample_id in sample_ids:
			obj, created = AnalysisResult.objects.get_or_create(
				submission=submission,
				sample_id=sample_id,
				defaults={"status": "pending"},
			)

			match_path = result_dir_map.get(sample_id.lower())
			if match_path:
				if obj.status != "finished" or obj.result_directory != match_path:
					obj.status = "finished"
					obj.result_directory = match_path
					obj.save(update_fields=["status", "result_directory"])


def main() -> None:
	setup_django()
	run()


if __name__ == "__main__":
	main()