from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db import transaction


ARCHIVE_INSTITUTION = "COGDAT (Archive)"
ARCHIVE_SUBMISSION_TYPE = "cogdat"
ARCHIVE_METADATA_FILENAME = "metadata_cogdat.csv"
ARCHIVE_JSON_FILENAME = "sampleID_nextclade.json"
ARCHIVE_JSON_DIRNAME = "json_files"


class Command(BaseCommand):
	help = "Create the COGDAT archive submission row and attach the archive files."

	def add_arguments(self, parser):
		parser.add_argument(
			"--source-root",
			type=str,
			default=None,
			help="Optional path to the cogdat directory. Defaults to the repo's cogdat folder.",
		)

	def handle(self, *args, **options):
		from gensurvapp.models import Submission, UploadedFile

		repo_root = Path(__file__).resolve().parents[4]
		source_root = Path(options["source_root"]).expanduser().resolve() if options["source_root"] else repo_root / "cogdat"
		metadata_path = source_root / ARCHIVE_METADATA_FILENAME
		json_dir = source_root / ARCHIVE_JSON_DIRNAME
		fasta_dir = source_root / "fasta_files"

		missing_paths = [path for path in [metadata_path, json_dir, fasta_dir] if not path.exists()]
		if missing_paths:
			for path in missing_paths:
				self.stderr.write(self.style.ERROR(f"Missing source path: {path}"))
			return

		User = get_user_model()
		user, created = User.objects.get_or_create(
			username="admin",
			defaults={
				"email": "admin@example.com",
				"institution": ARCHIVE_INSTITUTION,
				"is_staff": True,
				"is_superuser": True,
				"is_active": True,
			},
		)
		if not created and user.institution != ARCHIVE_INSTITUTION:
			user.institution = ARCHIVE_INSTITUTION
			user.save(update_fields=["institution"])

			existing_submission = (
			Submission.objects.filter(user=user, is_bulk_upload=True)
			.filter(files__file__icontains=ARCHIVE_METADATA_FILENAME)
			.distinct()
			.first()
		)

		with transaction.atomic():
			if existing_submission:
				submission = existing_submission
				# ensure submission_type is set to cogdat
				if submission.submission_type != ARCHIVE_SUBMISSION_TYPE:
					submission.submission_type = ARCHIVE_SUBMISSION_TYPE
					submission.save(update_fields=["submission_type"])
				self.stdout.write(self.style.WARNING(f"Updating existing archive submission {submission.id} with json files."))
			else:
				submission = Submission.objects.create(
					user=user,
					is_bulk_upload=True,
					resubmission_allowed=False,
					deletion_requested=False,
					submit_to_pipeline=False,
					submission_type=ARCHIVE_SUBMISSION_TYPE,
					metadata_warnings="",
					antibiotics_warnings="",
					fastq_warnings="",
					metadata_statistics={},
				)

			created_files = []

			# attach metadata if not already attached
			if not submission.files.filter(file__icontains=ARCHIVE_METADATA_FILENAME).exists():
				created_files.append(self._attach_file(submission, metadata_path, "metadata_raw", sample_id=""))

			# attach fasta files
			for fasta_path in sorted(fasta_dir.glob("*.fasta")):
				sample_id = self._sample_id_from_filename(fasta_path.name)
				if not submission.files.filter(file__icontains=fasta_path.name).exists():
					created_files.append(self._attach_file(submission, fasta_path, "fastq", sample_id=sample_id))

			# remove any old single-json file matching ARCHIVE_JSON_FILENAME
			old_json_files = list(submission.files.filter(file__icontains=ARCHIVE_JSON_FILENAME))
			for old in old_json_files:
				old.delete()

			# attach all json files from json_dir
			for json_path in sorted(json_dir.glob("*.json")):
				if not submission.files.filter(file__icontains=json_path.name).exists():
					created_files.append(
						self._attach_file(
							submission,
							json_path,
							"fastq",
							sample_id=self._sample_id_from_filename(json_path.name),
						)
					)

		self.stdout.write(self.style.SUCCESS(f"Created archive submission {submission.id} for user 'admin'."))
		self.stdout.write(self.style.SUCCESS(f"Attached {len(created_files)} file record(s)."))

	def _sample_id_from_filename(self, filename: str) -> str:
		stem = Path(filename).stem
		if stem.endswith("_assembly"):
			return stem[: -len("_assembly")]
		return stem

	def _attach_file(self, submission, source_path: Path, file_type: str, sample_id: str):
		from gensurvapp.models import UploadedFile

		uploaded = UploadedFile(submission=submission, file_type=file_type, sample_id=sample_id)
		with source_path.open("rb") as handle:
			uploaded.file.save(source_path.name, File(handle), save=False)
		uploaded.save()
		return uploaded