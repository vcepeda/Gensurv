

@login_required
def user_dashboard(request):
    logger.debug("Entering user_dashboard view")
    logger.debug(f"User: {request.user.username}")
    
    .filter(user=request.user).order_by('-created_at')
    logger.debug(f"Fetched {len(submissions)} submissions for user {request.user.username}")
    # Get counts of resubmissions per submission and file type
    history_counts = FileHistory.objects.values("submission_id", "file_type").annotate(count=Count("id"))

    # Convert to dict: {(submission_id, file_type): count}
    history_lookup = {
        (entry["submission_id"], entry["file_type"]): entry["count"]
        for entry in history_counts
    }

    context = []
    metadata_resub_count = 0
    antibiotics_resub_count = 0

###########
    # Build history_lookup → already fine

    # Build sample_ids once:
    all_sample_ids = set()

    for submission in submissions:
        for fastq_file in submission.uploadedfile_set.filter(file_type="fastq"):
            if fastq_file.sample_id:
                all_sample_ids.add(fastq_file.sample_id)

    # Fetch analysis results in ONE query:
    analysis_results = AnalysisResult.objects.filter(sample__sample_id__in=all_sample_ids).order_by('-completion_date')

    # Build lookup:
    analysis_lookup = {}
    for result in analysis_results:
        sample_id = result.sample.sample_id
        if sample_id not in analysis_lookup:
            analysis_lookup[sample_id] = result.status

###########
    for submission in submissions:
        logger.debug(f"▶️ Processing submission ID: {submission.id}")
        logger.debug(f"➡️ is_bulk_upload: {submission.is_bulk_upload}")
        logger.debug(f"➡️ resubmission_allowed: {submission.resubmission_allowed}")

        #"resubmission_allowed": submission.resubmission_allowed if submission else False,


        antibiotics_files = submission.uploadedfile_set.filter(file_type="antibiotics")
        fastq_files = submission.uploadedfile_set.filter(file_type="fastq")

        logger.debug(f"🧬 FASTQ count: {len(fastq_files)} | 🧫 Antibiotics file count: {len(antibiotics_files)}")

        sample_analysis_status = {}
        grouped_fastq_files = {}


        for fastq_file in fastq_files:
            sample_id = fastq_file.sample_id if fastq_file.sample_id else "unknown"
            grouped_fastq_files.setdefault(sample_id, []).append(fastq_file)

            if sample_id != "unknown":
                #analyses = AnalysisResult.objects.filter(sample__sample_id=sample_id)
                #status = analyses.order_by('-completion_date').first().status if analyses.exists() else "pending"
                status = analysis_lookup.get(sample_id, "pending")
                sample_analysis_status[sample_id] = status

        # Single submission metadata parsing
        
        sample_id = None
        if not submission.is_bulk_upload:
            cleaned_metadata = (
                submission.sample_files.filter(file_type="metadata_cleaned").first()
                or submission.uploadedfile_set.filter(file_type__in=["metadata_cleaned", "metadata"]).first()
            )
            logger.debug(f"🧼 Cleaned metadata found: {bool(cleaned_metadata)}")

            if cleaned_metadata and cleaned_metadata.file:
                try:
                    sample_id = parse_metadata_sample_ids(cleaned_metadata.file.path)
                    logger.debug(f"📍 Extracted sample_id from metadata: {sample_id}")
                except Exception as e:
                    logger.warning(f"❌ Error parsing sample_id: {e}")

                if sample_id:
                    grouped_fastq_files[sample_id] = list(fastq_files)
                    sample_analysis_status[sample_id] = "pending"

        logger.debug(f"📦 Grouped FASTQ Files: {grouped_fastq_files}")
        logger.debug(f"📊 Sample Analysis Status: {sample_analysis_status}")

        # Antibiotics Info
        antibiotics_info = {}

        if submission.is_bulk_upload:
            cleaned_metadata = (
                submission.sample_files.filter(file_type="metadata_cleaned").first()
                or submission.uploadedfile_set.filter(file_type__in=["metadata_cleaned", "metadata"]).first()
            )
            logger.debug(f"🧼 Bulk: Cleaned metadata file found: {bool(cleaned_metadata)}")

            if cleaned_metadata and cleaned_metadata.file:
                try:
                    full_info = parse_metadata_antibiotics_info(cleaned_metadata.file.path)
                    logger.debug(f"🔍 Parsed antibiotics_info from metadata: {full_info}")
                except Exception as e:
                    logger.warning(f"❌ Error parsing antibiotics info (bulk): {e}")
                    full_info = {}

                sample_ids_with_file = {f.sample_id for f in antibiotics_files if f.file}
                logger.debug(f"📛 Samples with antibiotics files: {sample_ids_with_file}")

                antibiotics_info = {
                    sample_id: info for sample_id, info in full_info.items()
                    if sample_id not in sample_ids_with_file
                }
                logger.debug(f"✅ Final antibiotics_info (bulk): {antibiotics_info}")

        elif not submission.is_bulk_upload:
            logger.debug("🔎 Attempting to parse antibiotics_info for single upload...")

            if not antibiotics_files.exists():
                cleaned_metadata = (
                    submission.sample_files.filter(file_type="metadata_cleaned").first()
                    or submission.uploadedfile_set.filter(file_type__in=["metadata_cleaned", "metadata"]).first()
                )
                logger.debug(f"🧼 Cleaned metadata exists: {bool(cleaned_metadata)}")

                if cleaned_metadata and cleaned_metadata.file:
                    # ✅ Make sure sample_id is parsed before checking
                    sample_id = sample_id or parse_metadata_sample_ids(cleaned_metadata.file.path)
                    if not sample_id:
                        logger.warning(f"❗ No sample_id could be extracted for submission {submission.id}")

                    logger.debug(f"🔬 Using sample_id for antibiotics info: {sample_id}")

                    if sample_id:
                        try:
                            info = parse_metadata_antibiotics_info(cleaned_metadata.file.path, target_sample_id=sample_id)
                            logger.debug(f"🧪 Antibiotics info extracted for sample {sample_id}: {info}")
                            if info:
                                antibiotics_info = {sample_id: info}
                        except Exception as e:
                            logger.warning(f"❌ Error parsing antibiotics info (single): {e}")
                    else:
                        logger.debug("⚠️ Skipped parsing: sample_id missing after fallback.")
            else:
                logger.debug("⛔ Skipping antibiotics info parse: antibiotics files already exist.")

        
        metadata_resub_count = history_lookup.get((submission.id, "metadata_raw"), 0)
        antibiotics_resub_count = history_lookup.get((submission.id, "antibiotics_raw"), 0)

        if submission.id == 119:
            for sample in sample_analysis_status:
                sample_analysis_status[sample] = "completed"
                

        context.append({
            'submission': submission,
            'antibiotics_files': antibiotics_files,
            'antibiotics_info': antibiotics_info,
            'grouped_fastq_files': grouped_fastq_files,
            'sample_analysis_status': sample_analysis_status,
            'metadata_resub_count': metadata_resub_count,
            'antibiotics_resub_count': antibiotics_resub_count,
        })

    logger.debug("✅ Finished building dashboard context")
    return render(request, 'gensurvapp/dashboard.html', {'submissions': context})
