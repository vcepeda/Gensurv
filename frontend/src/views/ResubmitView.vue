<template>
  <div class="container mt-4">
    <h2 class="mb-3">Resubmit Metadata</h2>
    <h3>Submission #{{ submissionId }}</h3>

    <!-- Success/Error Messages -->
    <div v-if="message" class="mt-3">
      <div
        :class="{
          'alert-danger': messageType === 'error',
          'alert-success': messageType === 'success',
          'alert-warning': messageType === 'warning',
          'alert-info': messageType === 'info'
        }"
        class="alert alert-dismissible fade show"
        role="alert"
      >
        <div v-html="message.replace(/\n/g, '<br>')"></div>
        <button type="button" class="btn-close" @click="message = null" aria-label="Close"></button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Submission Details -->
    <div v-else-if="row">
      <!-- Current Warnings -->
      <div v-if="metadataWarnings" class="alert alert-warning mt-3 p-3">
        <strong>Validation Warning:</strong><br />
        <pre class="mb-0" style="white-space: pre-wrap;">{{ metadataWarnings }}</pre>
      </div>

      <!-- Resubmit Form -->
      <div v-if="canResubmit" class="mt-4">
        <form @submit.prevent="handleResubmit">
          <div class="mb-3">
            <label for="metadataFile" class="form-label">
              <strong>Upload New {{ prettyFileType }} File</strong>
            </label>
            <input
              type="file"
              class="form-control"
              id="metadataFile"
              ref="fileInput"
              @change="handleFileChange"
              accept=".csv"
              required
            />
            <div class="form-text">
              Upload a corrected version of your {{ prettyFileType.toLowerCase() }} file (CSV format).
            </div>
          </div>

          <button type="submit" class="btn btn-warning" :disabled="uploading || !selectedFile">
            <span v-if="uploading">
              <span class="spinner-border spinner-border-sm me-2" role="status"></span>
              Uploading...
            </span>
            <span v-else>Upload New {{ prettyFileType }} File</span>
          </button>
        </form>
      </div>

      <!-- Already Valid -->
      <div v-else class="alert alert-info mt-3">
        ✅ This file was successfully validated and resubmission is no longer required.
      </div>

      <!-- File History -->
      <div v-if="history.length > 0" class="mt-5">
        <h4>Previous Versions:</h4>
        <ul class="list-group">
          <li
            v-for="entry in history"
            :key="entryKey(entry)"
            class="list-group-item"
          >
            <strong>{{ formatDate(entry.timestamp) }}</strong>
            <span v-if="entry.raw_url">
              -
              <a :href="entry.raw_url" target="_blank" rel="noopener">Raw</a>
            </span>
            <span v-if="entry.cleaned_url">
              | <a :href="entry.cleaned_url" target="_blank" rel="noopener">Cleaned</a>
            </span>
          </li>
        </ul>
      </div>
    </div>

    <div v-else-if="error" class="alert alert-danger mt-3">
      {{ error }}
    </div>

    <div class="mt-4">
      <router-link to="/dashboard" class="btn btn-secondary">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";

const route = useRoute();

const submissionId = ref(Number(route.params.submissionId));
const fileType = ref(route.params.fileType || "metadata");

const row = ref(null);
const history = ref([]);
const loading = ref(true);
const error = ref(null);

const selectedFile = ref(null);
const uploading = ref(false);

const message = ref(null);
const messageType = ref("info");

const fileInput = ref(null);

const prettyFileType = computed(() => {
  if (fileType.value === "metadata") return "Metadata";
  if (fileType.value === "antibiotics") return "Antibiotics";
  return fileType.value.charAt(0).toUpperCase() + fileType.value.slice(1);
});

const canResubmit = computed(() => {
  return !!row.value?.metadata?.can_resubmit;
});

const metadataWarnings = computed(() => {
  return row.value?.metadata?.warnings || "";
});

function entryKey(entry) {
  return `${entry.timestamp || ""}|${entry.raw_url || ""}|${entry.cleaned_url || ""}`;
}

async function fetchDashboardRow() {
  loading.value = true;
  error.value = null;

  try {
    const res = await apiClient.get("/api/dashboard/");
    const rows = Array.isArray(res.data) ? res.data : [];
    row.value = rows.find(r => Number(r.submission_id) === Number(submissionId.value)) || null;

    if (!row.value) {
      error.value = `Submission #${submissionId.value} not found (or you don't have access).`;
      history.value = [];
      return;
    }

    await fetchFileHistory();
  } catch (err) {
    console.error("Error fetching dashboard row:", err);
    error.value = "Failed to load submission details. Please try again.";
  } finally {
    loading.value = false;
  }
}

async function fetchFileHistory() {
  try {
    const res = await apiClient.get(
      `/api/submissions/${submissionId.value}/resubmissions/${fileType.value}/history/`
    );
    history.value = Array.isArray(res.data?.history) ? res.data.history : [];
  } catch (err) {
    console.error("Error fetching file history:", err);
    history.value = [];
  }
}

function handleFileChange(event) {
  const file = event.target.files?.[0];
  selectedFile.value = file || null;
}

async function handleResubmit() {
  if (!selectedFile.value) {
    showMessage("Please select a file to upload.", "error");
    return;
  }

  uploading.value = true;
  message.value = null;

  const formData = new FormData();
  formData.append("file", selectedFile.value);

  try {
    const res = await apiClient.post(
      `/api/submissions/${submissionId.value}/resubmissions/${fileType.value}/`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );

    const hasWarnings = !!res.data?.warnings;
    const msg = res.data?.message || "";

    if (hasWarnings) {
      showMessage(`File resubmitted with warnings:\n${msg}`, "warning");
    } else {
      showMessage("File resubmitted successfully.", "success");
    }

    await fetchDashboardRow();

    selectedFile.value = null;
    if (fileInput.value) fileInput.value.value = "";
  } catch (err) {
    console.error("Error resubmitting file:", err);
    const data = err.response?.data;
    const errorMsg =
      data?.detail ||
      data?.error ||
      data?.message ||
      "Failed to resubmit file. Please try again.";
    showMessage(errorMsg, "error");
  } finally {
    uploading.value = false;
  }
}

function showMessage(msg, type = "info") {
  message.value = msg;
  messageType.value = type;

  if (type === "success") {
    setTimeout(() => {
      message.value = null;
    }, 5000);
  }
}

function formatDate(dateString) {
  const d = new Date(dateString);
  return d.toLocaleString();
}

onMounted(() => {
  fetchDashboardRow();
});
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
