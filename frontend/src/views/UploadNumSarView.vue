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
                  {{ single.loading ? "Uploading..." : "Upload Single Sample" }}
                </button>
              </div>
            </form>

            <!-- messages -->
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
                  {{ bulk.loading ? "Uploading..." : "Upload Bulk Data" }}
                </button>
              </div>
            </form>

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
import apiClinet from "../api/client"
import { reactive, ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";

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

const single = reactive({
  metadata: null,
  fastq: [],
  submit_to_pipeline: false,
  loading: false,
  error: "",
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
  error: "",
  success: "",
  timing: null,
  submission_id: null,
  resubmission_allowed: false,
});

function onSingleMetadata(e) { single.metadata = e.target.files?.[0] ?? null; }
function onSingleFastq(e) { single.fastq = Array.from(e.target.files ?? []); }

function onBulkMetadata(e) { bulk.metadata = e.target.files?.[0] ?? null; }
function onBulkFastq(e) { bulk.fastq = Array.from(e.target.files ?? []); }

async function submitSingle() {
  single.loading = true;
  single.error = "";
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

  try {
    const res = await apiClinet.post(`/api/upload/single/?type=${uploadSubmissionType.value}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
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
    const data = err?.response?.data;
    single.error = data?.error || JSON.stringify(data?.errors || data || err.message, null, 2);
  } finally {
    single.loading = false;
  }
}

async function submitBulk() {
  bulk.loading = true;
  bulk.error = "";
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

  try {
    const res = await apiClinet.post(`/api/upload/bulk/?type=${uploadSubmissionType.value}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
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
    const data = err?.response?.data;
    bulk.error = data?.error || JSON.stringify(data?.errors || data || err.message, null, 2);
  } finally {
    bulk.loading = false;
  }
}
</script>
