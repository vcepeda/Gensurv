<template>
  <div class="container-fluid">
    <div v-if="!auth.isAuthenticated" class="text-center py-5">
      <h2>Login Required</h2>
      <p class="lead">To upload data please <RouterLink to="/login">login</RouterLink> to your account.</p>
    </div>
    
    <div v-else class="text-center mb-5">
      <h1 class="section-title text-center">Upload Your NUM-SAR Data Files</h1>
      <p class="lead">
        Choose between single sample upload or bulk upload options to upload your data.
      </p>
      <p>
        <RouterLink :to="helpLink">Click here</RouterLink>
        to view detailed help on NUM-SAR metadata and sequencing file formats.
      </p>
    </div>

    <div v-if="auth.isAuthenticated" class="row mb-4">
      <div class="col-lg-12">
        <div class="card shadow-sm">
          <div class="card-body">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-md-center gap-3">
              <span class="fw-semibold">Submission Type:</span>
              <div class="form-check form-check-inline">
                <input
                  class="form-check-input"
                  id="submission_type_bacteria"
                  type="radio"
                  value="bacteria"
                  v-model="submissionType"
                />
                <label class="form-check-label" for="submission_type_bacteria">Bacteria</label>
              </div>
              <div class="form-check form-check-inline">
                <input
                  class="form-check-input"
                  id="submission_type_virus"
                  type="radio"
                  value="virus"
                  v-model="submissionType"
                />
                <label class="form-check-label" for="submission_type_virus">Virus</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SINGLE -->
    <div v-if="auth.isAuthenticated" class="row">
      <div class="col-lg-12 mb-4">
        <div class="card shadow-sm accent-teal">
          <div class="card-header text-center">
            <h4><i class="fas fa-vial accent-icon me-2"></i>Single Sample Upload</h4>
          </div>
          <div class="card-body">
            <p>
              Use this option to upload data for a single sample. Include the metadata file
              and one or more sequencing files.
            </p>

            <form @submit.prevent="submitSingle">
              <div class="mb-3">
                <label class="form-label">Metadata file (required)</label>
                <input ref="singleMetadataInput" class="form-control" type="file" @change="onSingleMetadata" required />
              </div>

              <div class="mb-3">
                <label class="form-label">FASTQ files (required, one or more)</label>
                <input ref="singleFastqInput" class="form-control" type="file" multiple @change="onSingleFastq" required />
              </div>

              <div
                v-if="singleTotalSize > 0"
                class="mb-3 small"
                :class="singleTotalSize > MAX_SUBMISSION_SIZE_BYTES ? 'text-danger fw-bold' : 'text-muted'"
              >
                Total submission size: {{ formatBytes(singleTotalSize) }} / {{ formatBytes(MAX_SUBMISSION_SIZE_BYTES) }} limit
              </div>

              <div
                v-if="singleTotalSize > LARGE_UPLOAD_WARNING_THRESHOLD_BYTES && singleTotalSize <= MAX_SUBMISSION_SIZE_BYTES"
                class="alert alert-warning mt-2"
              >
                ⏳ This is a large submission ({{ formatBytes(singleTotalSize) }}). Depending on your network speed, the
                upload could take several hours. Please keep this browser tab open and prevent your computer from
                sleeping until it completes.
              </div>

              <div class="form-check mb-4" style="font-size: 1.1em; text-align: left;">
                <input
                  class="form-check-input"
                  id="single_pipeline"
                  type="checkbox"
                  v-model="single.submit_to_pipeline"
                />
                <label class="form-check-label" for="single_pipeline">
                  I want to submit this data to the bioinformatics analysis pipeline.
                </label>
              </div>

              <div class="text-center">
                <button class="btn btn-primary btn-lg mt-3" type="submit" :disabled="single.loading">
                  <i class="fas fa-upload"></i>
                  {{ single.loading ? (single.stage === "validating" ? "Validating..." : "Uploading...") : "Upload Single Sample" }}
                </button>
                <button
                  v-if="single.loading"
                  type="button"
                  class="btn btn-outline-danger btn-lg mt-3 ms-2"
                  @click="cancelSingle"
                >
                  Cancel
                </button>
              </div>

              <div v-if="single.loading && single.stage === 'uploading'">
                <div class="progress mt-3" style="height: 24px;">
                  <div
                    class="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    :style="{ width: single.progress + '%' }"
                    :aria-valuenow="single.progress"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  ></div>
                </div>
                <div class="text-center small fw-bold mt-1">
                  {{ single.progress }}%{{ single.eta ? ` — ${single.eta} remaining` : "" }}
                </div>
              </div>
            </form>

            <!-- messages -->
            <div v-if="single.cancelled" class="alert alert-secondary mt-3">
              <i class="fas fa-ban"></i>
              <span style="white-space: pre-wrap;"> {{ single.cancelled }} </span>
            </div>

            <div v-if="single.error" class="alert alert-danger mt-3">
              <i class="fas fa-exclamation-circle"></i>
              <span style="white-space: pre-wrap;"> {{ single.error }} </span>
            </div>

            <div v-if="single.success" class="alert alert-success mt-3">
              <i class="fas fa-check-circle"></i>
              <span style="white-space: pre-wrap;"> {{ single.success }} </span>
            </div>

            <div v-if="single.timing" class="alert alert-info mt-2">
              ✅ Total upload time: {{ single.timing.client_total_upload_time ?? "-" }}s<br />
              ⚙️ Processing duration (server): {{ single.timing.upload_duration }}s<br />
              📡 Upload + network delay: {{ single.timing.network_delay ?? "-" }}s
            </div>

            <div v-if="single.resubmission_allowed && single.submission_id" class="alert alert-warning mt-2">
              <i class="fas fa-exclamation-triangle"></i>
              <strong>Warning:</strong> Metadata validated with warnings. You may resubmit corrected metadata from your
              <RouterLink :to="`/dashboard#submission-${single.submission_id}`" class="alert-link">
                Submission #{{ single.submission_id }}
              </RouterLink>
              in the dashboard.
            </div>
          </div>
        </div>
      </div>

      <!-- BULK -->
      <div class="col-lg-12 mb-4">
        <div class="card shadow-sm accent-rose">
          <div class="card-header text-center">
            <h4><i class="fas fa-layer-group accent-icon me-2"></i>Bulk Upload</h4>
          </div>
          <div class="card-body">
            <p>If you have multiple samples to upload, use the bulk upload option below.</p>

            <form @submit.prevent="submitBulk">
              <div class="mb-3">
                <label class="form-label">Metadata file (required)</label>
                <input ref="bulkMetadataInput" class="form-control" type="file" @change="onBulkMetadata" required />
              </div>

              <div class="mb-3">
                <label class="form-label">FASTQ files (required, multiple)</label>
                <input ref="bulkFastqInput" class="form-control" type="file" multiple @change="onBulkFastq" required />
              </div>

              <div
                v-if="bulkTotalSize > 0"
                class="mb-3 small"
                :class="bulkTotalSize > MAX_SUBMISSION_SIZE_BYTES ? 'text-danger fw-bold' : 'text-muted'"
              >
                Total submission size: {{ formatBytes(bulkTotalSize) }} / {{ formatBytes(MAX_SUBMISSION_SIZE_BYTES) }} limit
              </div>

              <div
                v-if="bulkTotalSize > LARGE_UPLOAD_WARNING_THRESHOLD_BYTES && bulkTotalSize <= MAX_SUBMISSION_SIZE_BYTES"
                class="alert alert-warning mt-2"
              >
                ⏳ This is a large submission ({{ formatBytes(bulkTotalSize) }}). Depending on your network speed, the
                upload could take several hours. Please keep this browser tab open and prevent your computer from
                sleeping until it completes.
              </div>

              <div class="form-check mb-4" style="font-size: 1.1em; text-align: left;">
                <input
                  class="form-check-input"
                  id="bulk_pipeline"
                  type="checkbox"
                  v-model="bulk.submit_to_pipeline"
                />
                <label class="form-check-label" for="bulk_pipeline">
                  I want to submit this data to the bioinformatics analysis pipeline.
                </label>
              </div>

              <div class="text-center">
                <button class="btn btn-warning btn-lg mt-3" type="submit" :disabled="bulk.loading">
                  <i class="fas fa-file-upload"></i>
                  {{ bulk.loading ? (bulk.stage === "validating" ? "Validating..." : "Uploading...") : "Upload Bulk Data" }}
                </button>
                <button
                  v-if="bulk.loading"
                  type="button"
                  class="btn btn-outline-danger btn-lg mt-3 ms-2"
                  @click="cancelBulk"
                >
                  Cancel
                </button>
              </div>

              <div v-if="bulk.loading && bulk.stage === 'uploading'">
                <div class="progress mt-3" style="height: 24px;">
                  <div
                    class="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    :style="{ width: bulk.progress + '%' }"
                    :aria-valuenow="bulk.progress"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  ></div>
                </div>
                <div class="text-center small fw-bold mt-1">
                  {{ bulk.progress }}%{{ bulk.eta ? ` — ${bulk.eta} remaining` : "" }}
                </div>
              </div>
            </form>

            <div v-if="bulk.cancelled" class="alert alert-secondary mt-3">
              <i class="fas fa-ban"></i>
              <span style="white-space: pre-wrap;"> {{ bulk.cancelled }} </span>
            </div>

            <div v-if="bulk.error" class="alert alert-danger mt-3">
              <i class="fas fa-exclamation-circle"></i>
              <span style="white-space: pre-wrap;"> {{ bulk.error }} </span>
            </div>

            <div v-if="bulk.success" class="alert alert-success mt-3">
              <i class="fas fa-check-circle"></i>
              <span style="white-space: pre-wrap;"> {{ bulk.success }} </span>
            </div>

            <div v-if="bulk.timing" class="alert alert-info mt-2">
              ✅ Total upload time: {{ bulk.timing.client_total_upload_time ?? "-" }}s<br />
              ⚙️ Processing duration (server): {{ bulk.timing.upload_duration }}s<br />
              📡 Upload + network delay: {{ bulk.timing.network_delay ?? "-" }}s
            </div>

            <div v-if="bulk.resubmission_allowed && bulk.submission_id" class="alert alert-warning mt-2">
              <i class="fas fa-exclamation-triangle"></i>
              <strong>Warning:</strong> Metadata validated with warnings. You may resubmit corrected metadata from your
              <RouterLink :to="`/dashboard#submission-${bulk.submission_id}`" class="alert-link">
                Submission #{{ bulk.submission_id }}
              </RouterLink>
              in the dashboard.
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import axios from "axios";
import apiClinet from "../api/client"
import { reactive, ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import { toPrecheckFormData, extractErrorMessage } from "@/utils/uploadPrecheck";

const auth = useAuthStore();

// File input refs
const singleMetadataInput = ref(null);
const singleFastqInput = ref(null);
const bulkMetadataInput = ref(null);
const bulkFastqInput = ref(null);
const submissionType = ref("bacteria");

const helpLink = "/help/num-sar";

const uploadSubmissionType = computed(() => {
  return submissionType.value === "bacteria" ? "num-sar_bacteria" : "num-sar_virus";
});

let singleAbortController = null;
let bulkAbortController = null;

function cancelSingle() {
  singleAbortController?.abort();
}

function cancelBulk() {
  bulkAbortController?.abort();
}

const single = reactive({
  metadata: null,
  fastq: [],
  submit_to_pipeline: false,
  loading: false,
  stage: "",
  progress: 0,
  eta: "",
  error: "",
  cancelled: "",
  success: "",
  timing: null,
  submission_id: null,
  resubmission_allowed: false,
});

const bulk = reactive({
  metadata: null,
  fastq: [],
  submit_to_pipeline: false,
  loading: false,
  stage: "",
  progress: 0,
  eta: "",
  error: "",
  cancelled: "",
  success: "",
  timing: null,
  submission_id: null,
  resubmission_allowed: false,
});

const MAX_SUBMISSION_SIZE_BYTES = 100 * 1024 * 1024 * 1024; // 100 GB, matches the server's client_max_body_size
const LARGE_UPLOAD_WARNING_THRESHOLD_BYTES = 20 * 1024 * 1024 * 1024; // 20 GB, warn about long upload times

function formatBytes(bytes) {
  const gb = bytes / 1024 ** 3;
  if (gb >= 1) return `${gb.toFixed(2)} GB`;
  const mb = bytes / 1024 ** 2;
  return `${mb.toFixed(1)} MB`;
}

function formatDuration(seconds) {
  if (!isFinite(seconds) || seconds < 60) return "less than a minute";
  const totalMinutes = Math.round(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}

function getSubmissionSize(...fileGroups) {
  let total = 0;
  for (const group of fileGroups) {
    if (!group) continue;
    if (Array.isArray(group)) {
      total += group.reduce((sum, f) => sum + (f?.size || 0), 0);
    } else {
      total += group.size || 0;
    }
  }
  return total;
}

const singleTotalSize = computed(() => getSubmissionSize(single.metadata, single.fastq));
const bulkTotalSize = computed(() => getSubmissionSize(bulk.metadata, bulk.fastq));

function onSingleMetadata(e) { single.metadata = e.target.files?.[0] ?? null; }
function onSingleFastq(e) { single.fastq = Array.from(e.target.files ?? []); }

function onBulkMetadata(e) { bulk.metadata = e.target.files?.[0] ?? null; }
function onBulkFastq(e) { bulk.fastq = Array.from(e.target.files ?? []); }

async function submitSingle() {
  const totalSize = getSubmissionSize(single.metadata, single.fastq);
  if (totalSize > MAX_SUBMISSION_SIZE_BYTES) {
    single.error = `Your submission is ${formatBytes(totalSize)}, which exceeds the maximum allowed size of ${formatBytes(MAX_SUBMISSION_SIZE_BYTES)}. Please reduce the number/size of files and try again.`;
    return;
  }

  single.loading = true;
  single.error = "";
  single.cancelled = "";
  single.success = "";
  single.timing = null;
  single.submission_id = null;
  single.resubmission_allowed = false;

  const fd = new FormData();
  const start = Date.now() / 1000;

  fd.append("metadata_file", single.metadata);
  single.fastq.forEach((f) => fd.append("fastq_files", f));
  fd.append("submit_to_pipeline", String(single.submit_to_pipeline));
  fd.append("upload_start_time", String(start));

  singleAbortController = new AbortController();

  try {
    single.stage = "validating";
    await apiClinet.post(`/api/upload/single/?type=${uploadSubmissionType.value}&dry_run=true`, toPrecheckFormData(fd), {
      headers: { "Content-Type": "multipart/form-data" },
      signal: singleAbortController.signal,
    });
  } catch (err) {
    if (axios.isCancel(err)) {
      single.cancelled = "Upload cancelled.";
    } else {
      single.error = extractErrorMessage(err);
    }
    single.loading = false;
    single.stage = "";
    return;
  }

  try {
    single.stage = "uploading";
    single.progress = 0;
    single.eta = "";
    const uploadStartedAt = Date.now();
    const res = await apiClinet.post(`/api/upload/single/?type=${uploadSubmissionType.value}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      signal: singleAbortController.signal,
      onUploadProgress: (evt) => {
        if (!evt.total) return;
        single.progress = Math.round((evt.loaded / evt.total) * 100);
        const elapsedSec = (Date.now() - uploadStartedAt) / 1000;
        if (elapsedSec > 3 && evt.loaded > 0) {
          const rate = evt.loaded / elapsedSec;
          single.eta = formatDuration((evt.total - evt.loaded) / rate);
        }
      },
    });
    single.success = res.data.message;
    single.submission_id = res.data.submission_id;
    single.resubmission_allowed = !!res.data.resubmission_allowed;

    // Extract timing data from top-level response fields
    single.timing = {
      upload_duration: res.data.upload_duration ? Number(res.data.upload_duration.toFixed(2)) : null,
      client_total_upload_time: res.data.client_total_upload_time ? Number(res.data.client_total_upload_time.toFixed(2)) : Number((Date.now() / 1000 - start).toFixed(2)),
      network_delay: res.data.network_delay ? Number(res.data.network_delay.toFixed(2)) : null,
    };

    // Clear file inputs and data after successful upload
    single.submit_to_pipeline = false;
    single.metadata = null;
    single.fastq = [];
    if (singleMetadataInput.value) singleMetadataInput.value.value = "";
    if (singleFastqInput.value) singleFastqInput.value.value = "";
  } catch (err) {
    if (axios.isCancel(err)) {
      single.cancelled = "Upload cancelled.";
    } else {
      single.error = extractErrorMessage(err);
    }
  } finally {
    single.loading = false;
    single.stage = "";
    single.eta = "";
  }
}

async function submitBulk() {
  const totalSize = getSubmissionSize(bulk.metadata, bulk.fastq);
  if (totalSize > MAX_SUBMISSION_SIZE_BYTES) {
    bulk.error = `Your submission is ${formatBytes(totalSize)}, which exceeds the maximum allowed size of ${formatBytes(MAX_SUBMISSION_SIZE_BYTES)}. Please reduce the number/size of files and try again.`;
    return;
  }

  bulk.loading = true;
  bulk.error = "";
  bulk.cancelled = "";
  bulk.success = "";
  bulk.timing = null;
  bulk.submission_id = null;
  bulk.resubmission_allowed = false;

  const fd = new FormData();
  const start = Date.now() / 1000;

  fd.append("metadata_file", bulk.metadata);
  bulk.fastq.forEach((f) => fd.append("fastq_files", f));
  fd.append("submit_to_pipeline", String(bulk.submit_to_pipeline));
  fd.append("upload_start_time", String(start));

  bulkAbortController = new AbortController();

  try {
    bulk.stage = "validating";
    await apiClinet.post(`/api/upload/bulk/?type=${uploadSubmissionType.value}&dry_run=true`, toPrecheckFormData(fd), {
      headers: { "Content-Type": "multipart/form-data" },
      signal: bulkAbortController.signal,
    });
  } catch (err) {
    if (axios.isCancel(err)) {
      bulk.cancelled = "Upload cancelled.";
    } else {
      bulk.error = extractErrorMessage(err);
    }
    bulk.loading = false;
    bulk.stage = "";
    return;
  }

  try {
    bulk.stage = "uploading";
    bulk.progress = 0;
    bulk.eta = "";
    const uploadStartedAt = Date.now();
    const res = await apiClinet.post(`/api/upload/bulk/?type=${uploadSubmissionType.value}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      signal: bulkAbortController.signal,
      onUploadProgress: (evt) => {
        if (!evt.total) return;
        bulk.progress = Math.round((evt.loaded / evt.total) * 100);
        const elapsedSec = (Date.now() - uploadStartedAt) / 1000;
        if (elapsedSec > 3 && evt.loaded > 0) {
          const rate = evt.loaded / elapsedSec;
          bulk.eta = formatDuration((evt.total - evt.loaded) / rate);
        }
      },
    });
    bulk.success = res.data.message;
    bulk.submission_id = res.data.submission_id;
    bulk.resubmission_allowed = !!res.data.resubmission_allowed;
    
    // Extract timing data from top-level response fields
    bulk.timing = {
      upload_duration: res.data.upload_duration ? Number(res.data.upload_duration.toFixed(2)) : null,
      client_total_upload_time: res.data.client_total_upload_time ? Number(res.data.client_total_upload_time.toFixed(2)) : Number((Date.now() / 1000 - start).toFixed(2)),
      network_delay: res.data.network_delay ? Number(res.data.network_delay.toFixed(2)) : null,
    };

    // Clear file inputs and data after successful upload
    bulk.submit_to_pipeline = false;
    bulk.metadata = null;
    bulk.fastq = [];
    if (bulkMetadataInput.value) bulkMetadataInput.value.value = "";
    if (bulkFastqInput.value) bulkFastqInput.value.value = "";
  } catch (err) {
    if (axios.isCancel(err)) {
      bulk.cancelled = "Upload cancelled.";
    } else {
      bulk.error = extractErrorMessage(err);
    }
  } finally {
    bulk.loading = false;
    bulk.stage = "";
    bulk.eta = "";
  }
}
</script>
