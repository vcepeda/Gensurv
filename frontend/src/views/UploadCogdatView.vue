<template>
  <div class="container-fluid">
    <div v-if="!auth.isAuthenticated" class="text-center py-5">
      <h2>Login Required</h2>
      <p class="lead">To upload data please <RouterLink to="/login">login</RouterLink> to your account.</p>
    </div>

    <div v-else class="text-center mb-5">
      <h1 class="section-title text-center">Upload COGDAT FASTQ Files</h1>
      <p class="lead">
        Upload raw sequencing files for archival storage. No metadata file is needed - files are
        stored as-is and matched up with their samples manually afterwards.
      </p>
      <p>
        <RouterLink to="/help/cogdat">Click here</RouterLink>
        to view detailed help on COGDAT metadata columns.
      </p>
    </div>

    <div v-if="auth.isAuthenticated" class="row">
      <div class="col-lg-12 mb-4">
        <div class="card shadow-sm accent-teal">
          <div class="card-header text-center">
            <h4><i class="fas fa-dna accent-icon me-2"></i>FASTQ Upload</h4>
          </div>
          <div class="card-body">
            <p>
              Select one or more FASTQ files. No filename convention is enforced - files are
              accepted as-is and stored for archival purposes.
            </p>

            <form @submit.prevent="submitCogdat">
              <div class="mb-3">
                <label class="form-label">FASTQ files (required, one or more)</label>
                <input ref="fastqInput" class="form-control" type="file" multiple @change="onFastqChange" required />
              </div>

              <div
                v-if="totalSize > 0"
                class="mb-3 small"
                :class="totalSize > MAX_SUBMISSION_SIZE_BYTES ? 'text-danger fw-bold' : 'text-muted'"
              >
                Total submission size: {{ formatBytes(totalSize) }} / {{ formatBytes(MAX_SUBMISSION_SIZE_BYTES) }} limit
              </div>

              <div
                v-if="totalSize > LARGE_UPLOAD_WARNING_THRESHOLD_BYTES && totalSize <= MAX_SUBMISSION_SIZE_BYTES"
                class="alert alert-warning mt-2"
              >
                ⏳ This is a large submission ({{ formatBytes(totalSize) }}). Depending on your network speed, the
                upload could take several hours. Please keep this browser tab open and prevent your computer from
                sleeping until it completes.
              </div>

              <div class="text-center">
                <button class="btn btn-primary btn-lg mt-3" type="submit" :disabled="cogdat.loading">
                  <i class="fas fa-upload"></i>
                  {{ cogdat.loading ? (cogdat.stage === "validating" ? "Validating..." : "Uploading...") : "Upload FASTQ Files" }}
                </button>
                <button
                  v-if="cogdat.loading"
                  type="button"
                  class="btn btn-outline-danger btn-lg mt-3 ms-2"
                  @click="cancelCogdat"
                >
                  Cancel
                </button>
              </div>

              <div v-if="cogdat.loading && cogdat.stage === 'uploading'">
                <div class="progress mt-3" style="height: 24px;">
                  <div
                    class="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    :style="{ width: cogdat.progress + '%' }"
                    :aria-valuenow="cogdat.progress"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  ></div>
                </div>
                <div class="text-center small fw-bold mt-1">
                  {{ cogdat.progress }}%{{ cogdat.eta ? ` — ${cogdat.eta} remaining` : "" }}
                </div>
              </div>
            </form>

            <!-- messages -->
            <div v-if="cogdat.cancelled" class="alert alert-secondary mt-3">
              <i class="fas fa-ban"></i>
              <span style="white-space: pre-wrap;"> {{ cogdat.cancelled }} </span>
            </div>

            <div v-if="cogdat.error" class="alert alert-danger mt-3">
              <i class="fas fa-exclamation-circle"></i>
              <span style="white-space: pre-wrap;"> {{ cogdat.error }} </span>
            </div>

            <div v-if="cogdat.success" class="alert alert-success mt-3">
              <i class="fas fa-check-circle"></i>
              <span style="white-space: pre-wrap;"> {{ cogdat.success }} </span>
            </div>

            <div v-if="cogdat.timing" class="alert alert-info mt-2">
              ✅ Total upload time: {{ cogdat.timing.client_total_upload_time ?? "-" }}s<br />
              ⚙️ Processing duration (server): {{ cogdat.timing.upload_duration }}s<br />
              📡 Upload + network delay: {{ cogdat.timing.network_delay ?? "-" }}s
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from "axios";
import apiClinet from "../api/client";
import { reactive, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { toPrecheckFormData, extractErrorMessage } from "@/utils/uploadPrecheck";

const auth = useAuthStore();

const fastqInput = ref(null);
let cogdatAbortController = null;

function cancelCogdat() {
  cogdatAbortController?.abort();
}

const cogdat = reactive({
  fastq: [],
  loading: false,
  stage: "",
  progress: 0,
  eta: "",
  error: "",
  cancelled: "",
  success: "",
  timing: null,
  submission_id: null,
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

const totalSize = ref(0);

function onFastqChange(e) {
  cogdat.fastq = Array.from(e.target.files ?? []);
  totalSize.value = cogdat.fastq.reduce((sum, f) => sum + (f?.size || 0), 0);
}

async function submitCogdat() {
  if (totalSize.value > MAX_SUBMISSION_SIZE_BYTES) {
    cogdat.error = `Your submission is ${formatBytes(totalSize.value)}, which exceeds the maximum allowed size of ${formatBytes(MAX_SUBMISSION_SIZE_BYTES)}. Please reduce the number/size of files and try again.`;
    return;
  }

  cogdat.loading = true;
  cogdat.error = "";
  cogdat.cancelled = "";
  cogdat.success = "";
  cogdat.timing = null;
  cogdat.submission_id = null;

  const fd = new FormData();
  const start = Date.now() / 1000;

  cogdat.fastq.forEach((f) => fd.append("fastq_files", f));
  fd.append("upload_start_time", String(start));

  cogdatAbortController = new AbortController();

  try {
    cogdat.stage = "validating";
    await apiClinet.post("/api/upload/cogdat/?dry_run=true", toPrecheckFormData(fd), {
      headers: { "Content-Type": "multipart/form-data" },
      signal: cogdatAbortController.signal,
    });
  } catch (err) {
    if (axios.isCancel(err)) {
      cogdat.cancelled = "Upload cancelled.";
    } else {
      cogdat.error = extractErrorMessage(err);
    }
    cogdat.loading = false;
    cogdat.stage = "";
    return;
  }

  try {
    cogdat.stage = "uploading";
    cogdat.progress = 0;
    cogdat.eta = "";
    const uploadStartedAt = Date.now();
    const res = await apiClinet.post("/api/upload/cogdat/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
      signal: cogdatAbortController.signal,
      onUploadProgress: (evt) => {
        if (!evt.total) return;
        cogdat.progress = Math.round((evt.loaded / evt.total) * 100);
        const elapsedSec = (Date.now() - uploadStartedAt) / 1000;
        if (elapsedSec > 3 && evt.loaded > 0) {
          const rate = evt.loaded / elapsedSec;
          cogdat.eta = formatDuration((evt.total - evt.loaded) / rate);
        }
      },
    });
    cogdat.success = res.data.message;
    cogdat.submission_id = res.data.submission_id;

    cogdat.timing = {
      upload_duration: res.data.upload_duration ? Number(res.data.upload_duration.toFixed(2)) : null,
      client_total_upload_time: res.data.client_total_upload_time ? Number(res.data.client_total_upload_time.toFixed(2)) : Number((Date.now() / 1000 - start).toFixed(2)),
      network_delay: res.data.network_delay ? Number(res.data.network_delay.toFixed(2)) : null,
    };

    cogdat.fastq = [];
    totalSize.value = 0;
    if (fastqInput.value) fastqInput.value.value = "";
  } catch (err) {
    if (axios.isCancel(err)) {
      cogdat.cancelled = "Upload cancelled.";
    } else {
      cogdat.error = extractErrorMessage(err);
    }
  } finally {
    cogdat.loading = false;
    cogdat.stage = "";
    cogdat.eta = "";
  }
}
</script>
