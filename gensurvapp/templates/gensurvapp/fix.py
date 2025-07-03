        elif "bulk_upload" in request.POST:
            bulk_form = BulkUploadForm(request.POST, request.FILES)
            bulk_error_message = None
            if bulk_form.is_valid():
                try:
                    metadata_file = bulk_form.cleaned_data.get('metadata_file')
                    if metadata_file:
                        logger.debug(f"Processing uploaded bulk metadata file: {metadata_file.name} (type: {type(metadata_file)})")
                    else:
                        raise ValueError("Metadata file is required but not provided.")

                    uploaded_antibiotics_files = request.FILES.getlist('antibiotics_files')
                    if uploaded_antibiotics_files:
                        logger.debug(f"Processing {len(uploaded_antibiotics_files)} uploaded antibiotics file(s).")
                        for i, ab_file in enumerate(uploaded_antibiotics_files):
                            logger.debug(f"• Antibiotics file #{i+1}: {ab_file.name} (type: {type(ab_file)})")
                    else:
                        logger.debug("No antibiotics files uploaded.")

                    fastq_files = request.FILES.getlist('fastq_files')
                    if not fastq_files:
                        raise ValueError(f"At least one sequencing file must be provided.")
                    else:
                        logger.debug(f"Processing {len(fastq_files)} uploaded FASTQ file(s).")
                        for i, fastq_file in enumerate(fastq_files):
                            logger.debug(f"Processing #${i+1} uploaded FASTQ file: {fastq_file.name} (type: {type(fastq_file)})")

                    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(metadata_file, METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS)
                    logger.debug(f"Detected delimiter: {detected_delimiter_meta}")

                    if not valid_metadata:
                        raise ValueError(f"Metadata file error: {metadata_message}")
                    elif metadata_warning:
                        warning_message = f"Warnings in metadata file:\n{metadata_message}"
                        logger.debug(f"Metadata file validated with warnings: {warning_message}")
                    else:
                        logger.debug(f"Metadata file validated successfully: {metadata_file.name}")

                    if metadata_df.empty:
                        bulk_error_message = "Metadata file is empty or incorrectly formatted."
                        raise ValueError(bulk_error_message)

                    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
                    logger.debug("Normalize column names (fixes unexpected whitespace or case issues")

                    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
                    uploaded_fastq_files_names = {f.name.strip() for f in fastq_files}
                    logger.debug(f"📁 Uploaded FASTQ filenames: {uploaded_fastq_files_names}")

                    all_expected_fastq_files = set()

                    for idx, row in metadata_df.iterrows():
                        sample_id = str(row.get("sample identifier", f"row {idx + 1}")).strip()

                        if not sample_id or sample_id.lower() == 'nan':
                            logger.debug(f"Row {idx + 1}: Missing or invalid sample identifier.")
                            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

                        illumina_r1 = row["illumina r1"].strip() if pd.notna(row.get("illumina r1")) else None
                        illumina_r2 = row["illumina r2"].strip() if pd.notna(row.get("illumina r2")) else None
                        nanopore    = row["nanopore"].strip()    if pd.notna(row.get("nanopore")) else None
                        pacbio      = row["pacbio"].strip()      if pd.notna(row.get("pacbio")) else None

                        expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]
                        all_expected_fastq_files.update(expected_fastq_files)

                        logger.debug(f"📋 Final list of expected FASTQ files for sample {sample_id}: {expected_fastq_files}")

                        if not any([illumina_r1, nanopore, pacbio]):
                            raise ValueError(f"Sample '{sample_id}': Must include at least one platform file (Illumina R1, Nanopore, or PacBio).")
                        if illumina_r2 and not illumina_r1:
                            raise ValueError(f"Sample '{sample_id}': Illumina R2 file provided without Illumina R1.")

                        for file in expected_fastq_files:
                            if not any(file.lower().endswith(valid_ext) for valid_ext in valid_extensions):
                                raise ValueError(
                                    f"Sample '{sample_id}': File '{file}' has an invalid extension.\n"
                                    f"Allowed extensions: {', '.join(valid_extensions)}"
                                )

                        missing_fastq_files = set(expected_fastq_files) - uploaded_fastq_files_names
                        if missing_fastq_files:
                            raise ValueError(
                                f"Sample '{sample_id}': Some FASTQ files listed in metadata are missing from the upload.\n"
                                f"Missing: {', '.join(sorted(missing_fastq_files))}\n"
                                f"Expected: {', '.join(expected_fastq_files)}\n"
                                f"Uploaded: {', '.join(sorted(uploaded_fastq_files_names))}"
                            )

                        logger.info(f"✅ Sample '{sample_id}': All expected FASTQ files validated successfully.")

                    # Global extra FASTQ check
                    extra_fastq_files = uploaded_fastq_files_names - all_expected_fastq_files
                    extra_fastq_warning = ""
                    if extra_fastq_files:
                        logger.warning(f"⚠️ Extra FASTQ files detected (ignored): {', '.join(extra_fastq_files)}")
                        extra_fastq_warning = f"⚠️ Warning: Extra FASTQ file(s) were uploaded but ignored: {', '.join(extra_fastq_files)}."

                    # [Rest of your view remains unchanged]
