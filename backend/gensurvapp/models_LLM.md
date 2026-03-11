## Overview

This version of `models.py` represents a **deliberate simplification and normalization** of the data model to align with how the backend actually behaves today.

The guiding principles were:

1. **Single source of truth for uploaded files**
2. **Submission as a workflow container, not a file holder**
3. **Warnings are diagnostics, not entities**
4. **Explicit, persisted user intent**
5. **Scalable pipeline results without table explosion**

No changes were made lightly — each change fixes a concrete mismatch between schema and backend logic.

---

## High-level changes summary

### Removed

* `SampleFile` model
* Direct file storage on `Submission` (e.g. `metadata_file`)
* Tool-specific result tables (`AnalysisResult`, `BactopiaResult`, `PlasmidIdentResult`)

### Added / Reworked

* `UploadedFile` as the **only file table**
* `PipelineResult` as a **unified pipeline output table**
* Submission-level warning fields
* Explicit `submit_to_pipeline` intent flag

---

## Detailed changes & rationale

---

## 1️⃣ `Submission` model

### What changed

* Removed any direct file fields
* Kept only **workflow, warnings, and timing**
* Explicitly stores `submit_to_pipeline`
* Holds separate warning fields:

  * `fastq_warnings`
  * `extra_fastq_warnings`

### Why

`Submission` is a **logical unit of work**, not a file container.

In practice:

* Files are uploaded, cleaned, versioned, and queried independently
* Submissions group files, warnings, and pipeline intent
* Warnings are submission-level diagnostics, not relational objects

### Design decision

Warnings are stored as **plain text blobs**, because:

* they are not queried structurally
* they are append-only diagnostics
* they map 1-to-1 with user feedback and UI display

Keeping `fastq_warnings` and `extra_fastq_warnings` separate preserves an important semantic distinction:

* **FASTQ issues** → problems with expected inputs
* **Extra FASTQs** → ignored / unexpected inputs

---

## 2️⃣ `user_submission_path`

### What changed

* Path logic generalized to:

  * `Submission`
  * any model with `.submission`

### Why

This allows:

* consistent file layout
* reuse across `UploadedFile`, `FileHistory`, `PipelineResult`
* no duplicated path logic

### Result

All artifacts for a submission live under:

```
submissions/<username>/submission_<id>/
```

This makes filesystem inspection, cleanup, and debugging trivial.

---

## 3️⃣ `UploadedFile` (core refactor)

### What changed

* `UploadedFile` is now the **only file table**
* Stores:

  * raw file
  * optional cleaned file
  * `file_type` (free text)
  * `sample_id` (optional)

### Why

Previously:

* `SampleFile` and `UploadedFile` represented the same concept
* Different parts of the backend used different tables
* This caused mental overhead and potential inconsistency

Now:

* Every uploaded artifact lives in **one table**
* The dashboard, upload service, and result logic all query the same model

### Why `file_type` and `sample_id` are free-text

This was intentional:

* avoids premature constraints
* allows rapid iteration
* backend logic already assumes string comparisons
* avoids migrations for vocabulary changes

Validation belongs in **service logic**, not the schema.

---

## 4️⃣ Removal of `SampleFile`

### What changed

* `SampleFile` was deleted entirely

### Why

It was:

* semantically identical to `UploadedFile`
* unused as a true abstraction
* a source of duplicated queries and confusion

Deleting it:

* simplified dashboard queries
* removed an unnecessary join layer
* forced consistency across services

---

## 5️⃣ `FileHistory`

### What changed

* Stores **paths**, not managed `FileField`s
* Explicitly records resubmission history

### Why

History entries are:

* archival
* not actively served
* often written programmatically

Storing paths avoids Django file-handling edge cases and makes historical reconstruction easier.

---

## 6️⃣ Unified `PipelineResult`

### What changed

Replaced:

* `AnalysisResult`
* `BactopiaResult`
* `PlasmidIdentResult`

With:

* **one table**: `PipelineResult`

### Why

Tool-specific result tables do not scale.

Every new pipeline would otherwise require:

* a new model
* new migrations
* new queries
* new dashboard logic

`PipelineResult` solves this by:

* normalizing pipeline identity (`pipeline`)
* keeping per-sample, per-submission uniqueness
* supporting arbitrary future tools without schema changes

### Conceptual model

```
Submission
  └── Sample
        └── Pipeline (bactopia / plasmident / etc.)
              └── Result
```

This matches how analysis actually works.

---

## 7️⃣ Indexes & constraints (intentional)

Indexes and uniqueness constraints were added **only where they encode invariants**, not business rules.

Examples:

* one metadata file per submission
* one pipeline result per (submission, sample, pipeline)

They exist to:

* prevent silent data corruption
* simplify query logic
* surface bugs early

They do **not** encode workflow logic.

---

## Migration notes (important)

This refactor required a schema migration because:

* `SampleFile` was removed
* `AnalysisResult` was replaced
* `sample_id` became a required field

For existing data:

* legacy rows were populated with a one-off default (`"unknown"`)
* this preserves referential integrity without blocking development

This is acceptable because:

* old analysis rows are not critical to current workflows
* new rows are always created with explicit `sample_id`

---

## Final rationale (why this version exists)

This model version exists to ensure:

* ✅ Schema matches backend reality
* ✅ No duplicated representations of the same concept
* ✅ Clear ownership of responsibilities
* ✅ Easy extension to new pipelines
* ✅ Minimal cognitive overhead for future development

