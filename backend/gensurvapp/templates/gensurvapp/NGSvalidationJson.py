            # Special case for NGS validation
            #if "sequencing platform" in df.columns and "ngs files" in df.columns:
                for index, row in df.iterrows():
                    sample_id = row.get("sample identifier", f"Row {index + 1}")

                    # Ensure sequencing platform and NGS files exist
                    sequencing_platforms = str(row.get("sequencing platform", "")).strip()
                    ngs_files_raw = str(row.get("ngs files", "")).strip()

                    logger.debug(f"Row {index + 1} - Sample ID: {sample_id}")
                    logger.debug(f"Row {index + 1} - Raw Sequencing Platform: {sequencing_platforms}")
                    logger.debug(f"Row {index + 1} - Raw NGS Files: {ngs_files_raw}")

                    # Skip row if `NGS Files` is empty
                    if not ngs_files_raw:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(
                            f"Row {index + 1}: 'NGS Files' is missing or empty."
                        )
                        logger.error(f"Row {index + 1}: Missing 'NGS Files'.")
                        continue

                    # Attempt to parse `NGS Files` as JSON
                    try:
                        parsed_ngs_files = json.loads(ngs_files_raw.replace("'", '"').strip())  # Handle single-quote cases
                    except json.JSONDecodeError:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(
                            f"Row {index + 1}: 'NGS Files' contains invalid JSON format."
                        )
                        logger.error(f"Row {index + 1}: Invalid JSON format in 'NGS Files'.")
                        continue

                    # Debug: Print parsed JSON structure
                    logger.debug(f"Row {index + 1} - Parsed NGS Files: {parsed_ngs_files}")

                    # Normalize platforms for comparison
                    platforms_list = {p.strip().lower() for p in sequencing_platforms.split(",") if p.strip()}
                    ngs_keys = {k.strip().lower() for k in parsed_ngs_files.keys()}

                    # Debug: Print comparison sets
                    logger.debug(f"Row {index + 1} - Normalized Platforms Set: {platforms_list}")
                    logger.debug(f"Row {index + 1} - NGS File Keys Set: {ngs_keys}")

                    # Validate that platforms match keys in NGS Files
                    if platforms_list != ngs_keys:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(
                            f"Row {index + 1}: 'Sequencing Platform' does not match keys in 'NGS Files'. Expected {platforms_list}, found {ngs_keys}."
                        )
                        logger.error(f"Row {index + 1}: Platform mismatch - Expected {platforms_list}, Found {ngs_keys}")
                        continue

                    # Validate file types for each platform
                    for platform, files in parsed_ngs_files.items():
                        files = [f.strip() for f in files if f.strip()]  # Clean file paths

                        if platform.lower() == "illumina":
                            if len(files) not in [1, 2]:
                                validation_results["is_valid"] = False
                                validation_results["type_mismatches"].append(
                                    f"Row {index + 1} (Illumina): Expected 1 (single-end) or 2 (paired-end) files, found {len(files)}."
                                )
                        elif platform.lower() in ["nanopore", "pacbio"]:
                            invalid_files = [f for f in files if not f.endswith((".fastq", ".fq", ".bam"))]
                            if invalid_files:
                                validation_results["is_valid"] = False
                                validation_results["type_mismatches"].append(
                                    f"Row {index + 1} ({platform}): Invalid file types {invalid_files}."
                                )
                        elif platform.lower() == "hybrid":
                            if not files:
                                validation_results["is_valid"] = False
                                validation_results["type_mismatches"].append(
                                    f"Row {index + 1} (Hybrid): No files provided for hybrid sequencing."
                                )
#######