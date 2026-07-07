<template>
  <div class="container-fluid submissions-page">
    <div v-if="!authStore.isAuthenticated" class="text-center py-5">
      <h2>Login Required</h2>
      <p class="lead">
        To view your dashboard please <RouterLink to="/login">login</RouterLink> to your account.
      </p>
    </div>

    <template v-else>
      <div class="mb-4">
        <h1 class="text-center mb-2">Submissions</h1>
        <p class="lead text-center mb-2">
          View uploaded data, including metadata, antibiotic files, FASTQ files, and their analysis statuses.
        </p>

        <div v-if="showScopeToggle" class="scope-toggle-wrap">
          <div class="btn-group" role="group" aria-label="Dashboard scope toggle">
            <input
              id="scope-mine"
              v-model="selectedScope"
              class="btn-check"
              type="radio"
              name="dashboard-scope"
              value="mine"
              autocomplete="off"
            />
            <label class="btn btn-outline-primary btn-sm" for="scope-mine">Your submissions</label>

            <input
              id="scope-others"
              v-model="selectedScope"
              class="btn-check"
              type="radio"
              name="dashboard-scope"
              value="others"
              autocomplete="off"
            />
            <label class="btn btn-outline-primary btn-sm" for="scope-others">Other's submissions</label>
          </div>
        </div>
      </div>

      <div class="card shadow-sm dashboard-card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span class="fw-semibold">Submission Details</span>
          <button class="btn btn-outline-secondary btn-sm" @click="fetchRows" :disabled="loading">
            Refresh
          </button>
        </div>

        <div class="card-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>

          <div v-if="!loading && enrichedRows.length === 0" class="text-center py-5">
            <h5 class="text-muted mb-3">
              {{ selectedScope === "others" ? "No other submissions available" : "You don't have any submissions" }}
            </h5>
            <router-link v-if="selectedScope !== 'others'" to="/upload" class="btn btn-primary">Upload Data</router-link>
          </div>

          <div v-else class="table-responsive compact-table-wrap">
            <table class="table table-sm table-hover align-middle compact-table">
              <thead class="table-light sticky-header">
                <tr>
                  <th>Username</th>
                  <th>Institution</th>
                  <th>Submission</th>
                  <th>Created</th>
                  <th>Metadata File</th>
                  <th class="actions-col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in enrichedRows"
                  :key="row.submission_id"
                  :id="`submission-${row.submission_id}`"
                >
                  <td class="text-nowrap">{{ row.username || "-" }}</td>

                  <td>
                    <span class="institution-text">{{ row.institution || "-" }}</span>
                  </td>

                  <td>
                    <div class="fw-semibold">#{{ row.submission_id }}</div>
                    <span
                      class="badge"
                      :class="row.submission_type === 'virus' ? 'text-bg-primary' : 'text-bg-success'"
                    >
                      {{ row.submission_type || "bacteria" }}
                    </span>
                  </td>

                  <td>
                    <div class="created-date">{{ formatDateParts(row.created_at).date }}</div>
                    <div class="created-time">{{ formatDateParts(row.created_at).time }}</div>
                  </td>

                  <td>
                    <div class="metadata-cell">
                      <div v-if="row.metadata?.files?.cleaned_url" class="metadata-line">
                        <span class="metadata-label">Clean:</span>
                        <a v-if="canDownloadCurrentScope"
                          :href="metadataViewerHref(row.metadata.files.cleaned_url, row.metadata.files.cleaned_name)"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="metadata-link"
                        >
                          {{ row.metadata.files.cleaned_name }}
                        </a>
                        <span v-else class="metadata-link text-muted">{{ row.metadata.files.cleaned_name }}</span>
                      </div>
                      <div v-if="row.metadata?.files?.raw_url" class="metadata-line">
                        <span class="metadata-label">Raw:</span>
                        <a v-if="canDownloadCurrentScope"
                          :href="metadataViewerHref(row.metadata.files.raw_url, row.metadata.files.raw_name)"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="metadata-link"
                        >
                          {{ row.metadata.files.raw_name }}
                        </a>
                        <span v-else class="metadata-link text-muted">{{ row.metadata.files.raw_name }}</span>
                      </div>
                      <span
                        v-if="!row.metadata?.files?.raw_url && !row.metadata?.files?.cleaned_url"
                        class="text-muted"
                      >
                        N/A
                      </span>

                      <div class="metadata-actions">
                        <button
                          v-if="getWarningCount(row.metadata?.warnings) > 0"
                          class="btn btn-warning btn-sm metadata-chip"
                          type="button"
                          title="Show metadata warnings"
                          aria-label="Show metadata warnings"
                          @click="openWarningModal(row, 'Metadata Warning', row.metadata?.warnings, true)"
                        >
                          Metadata Warning
                        </button>
                        <RouterLink
                          class="btn btn-info btn-sm metadata-chip"
                          :to="{ name: 'metadata_statistics', params: { submissionId: row.submission_id } }"
                        >
                          View Statistics
                        </RouterLink>
                      </div>
                    </div>
                  </td>

                  <td>
                    <div class="d-flex flex-wrap gap-2 action-group">
                      <button class="btn btn-outline-primary btn-sm" @click="openSubmissionDetails(row)">
                        View Submission
                      </button>
                      <RouterLink
                        class="btn btn-primary btn-sm"
                        :class="{ disabled: !hasCompletedStatus(row) }"
                        :to="{ name: 'submission_results', params: { submissionId: row.submission_id } }"
                        :aria-disabled="!hasCompletedStatus(row)"
                        :title="!hasCompletedStatus(row) ? 'Results not availanle' : 'View Results'"
                        @click="!hasCompletedStatus(row) && $event.preventDefault()"
                      >
                        View Results
                      </RouterLink>
                      <button
                        v-if="!isOthersScope && !row.deletion?.requested"
                        class="btn btn-danger btn-sm"
                        @click="requestDeletion(row.submission_id)"
                      >
                        Request Deletion
                      </button>
                      <span v-else-if="!isOthersScope" class="badge text-bg-secondary deletion-chip">Deletion Requested</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="loading" class="text-muted">Loading…</div>
        </div>
      </div>
    </template>

    <div v-if="activeWarning" class="overlay" @click.self="closeWarningModal">
      <div class="overlay-panel warning-modal" role="dialog" aria-modal="true" aria-label="Warning details">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h5 class="mb-0">{{ activeWarning.title }} for #{{ activeWarning.submissionId }}</h5>
          <button class="btn-close" @click="closeWarningModal" aria-label="Close"></button>
        </div>
        <div v-if="activeWarning.showResubmit && activeWarning.canResubmit" class="mb-3">
          <RouterLink
            class="btn btn-warning btn-sm"
            :to="{
              name: 'resubmit',
              params: { submissionId: activeWarning.submissionId, fileType: 'metadata' },
            }"
            @click="closeWarningModal"
          >
            Resubmit Metadata
          </RouterLink>
        </div>
        <pre class="warning-text">{{ activeWarning.message }}</pre>
      </div>
    </div>

    <div v-if="selectedSubmission" class="overlay side-drawer-wrap" @click.self="closeSubmissionDetails">
      <aside class="overlay-panel side-drawer" role="dialog" aria-modal="true" aria-label="Submission details">
        <div class="drawer-header">
          <div>
            <h4 class="mb-1">Submission #{{ selectedSubmission.submission_id }}</h4>
            <div class="text-muted small">{{ formatDate(selectedSubmission.created_at) }}</div>
          </div>
          <button class="btn-close" @click="closeSubmissionDetails" aria-label="Close"></button>
        </div>

        <section class="drawer-section">
          <h6>Antibiotics Files</h6>
          <template v-if="selectedSubmission.antibiotics?.files?.length">
            <div
              v-for="f in selectedSubmission.antibiotics.files"
              :key="f.sample_id + (f.raw_url || '')"
              class="small mb-2"
            >
              <div class="fw-semibold">{{ f.sample_id }}</div>
              <div v-if="f.raw_url">
                <a v-if="canDownloadCurrentScope" :href="f.raw_url" target="_blank" rel="noopener noreferrer">{{ f.raw_name }}</a>
                <span v-else class="text-muted">{{ f.raw_name }}</span>
              </div>
              <div v-if="f.cleaned_url">
                <a v-if="canDownloadCurrentScope" :href="f.cleaned_url" target="_blank" rel="noopener noreferrer">{{ f.cleaned_name }}</a>
                <span v-else class="text-muted">{{ f.cleaned_name }}</span>
              </div>
            </div>
          </template>
          <div v-else class="text-muted small">No antibiotics files</div>
        </section>

        <section class="drawer-section">
          <h6>FASTQ Files</h6>
          <template v-if="selectedSubmission.fastq?.grouped && Object.keys(selectedSubmission.fastq.grouped).length">
            <div v-for="(files, sid) in selectedSubmission.fastq.grouped" :key="sid" class="small mb-2">
              <div class="fw-semibold">{{ sid }}</div>
              <div v-for="f in files" :key="f.url">
                <a v-if="canDownloadCurrentScope" :href="f.url" target="_blank" rel="noopener noreferrer">{{ f.name }}</a>
                <span v-else class="text-muted">{{ f.name }}</span>
              </div>
            </div>
          </template>
          <div v-else class="text-muted small">No FASTQ files</div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import apiClient from "../api/client/";
import { useAuthStore } from "@/stores/auth";

const rows = ref([]);
const loading = ref(false);
const error = ref("");
const selectedSubmission = ref(null);
const activeWarning = ref(null);
const selectedScope = ref("mine");

const authStore = useAuthStore();
const showScopeToggle = computed(() => !authStore.isSuperuser && !authStore.isStaff);
const isOthersScope = computed(() => selectedScope.value === "others");
const canDownloadCurrentScope = computed(() => !isOthersScope.value || authStore.isSuperuser);

const enrichedRows = computed(() => {
  return rows.value.map((row) => {
    return {
      ...row,
    };
  });
});

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString();
}

function formatDateParts(iso) {
  if (!iso) return { date: "", time: "" };
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString(),
    time: d.toLocaleTimeString(),
  };
}

function metadataViewerHref(fileUrl, fileName) {
  const params = new URLSearchParams({
    fileUrl: String(fileUrl || ""),
    fileName: String(fileName || ""),
  });
  return `/metadata-file-view?${params.toString()}`;
}

function hasCompletedStatus(row) {
  const statuses = Object.values(row.analysis?.statuses || {});
  return statuses.some((status) => status === "completed" || status === "finished");
}

function warningToText(rawWarning) {
  if (!rawWarning) return "";
  if (typeof rawWarning === "string") return rawWarning;
  if (Array.isArray(rawWarning)) return rawWarning.map((item) => String(item)).join("\n");
  return JSON.stringify(rawWarning, null, 2);
}

function getWarningCount(rawWarning) {
  const text = warningToText(rawWarning).trim();
  if (!text) return 0;
  return text.split(/\n+/).filter((line) => line.trim().length > 0).length;
}

function openWarningModal(row, title, rawWarning, showResubmit = false) {
  activeWarning.value = {
    title,
    submissionId: row.submission_id,
    message: warningToText(rawWarning) || "No warning details available.",
    showResubmit,
    canResubmit: !!row.metadata?.can_resubmit,
  };
}

function closeWarningModal() {
  activeWarning.value = null;
}

function openSubmissionDetails(row) {
  selectedSubmission.value = row;
}

function closeSubmissionDetails() {
  selectedSubmission.value = null;
}

async function fetchRows() {
  if (loading.value) return;

  error.value = "";
  loading.value = true;

  try {
    const params = {};
    if (!authStore.isSuperuser) {
      params.scope = selectedScope.value;
    }

    const res = await apiClient.get("/api/dashboard/", { timeout: 15000, params });
    rows.value = Array.isArray(res.data) ? res.data : [];
    if (!Array.isArray(res.data)) {
      error.value = "Unexpected dashboard response.";
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load submissions.";
  } finally {
    loading.value = false;
  }
}

async function requestDeletion(submissionId) {
  if (!confirm("Are you sure you want to request deletion of this submission?")) return;

  try {
    await apiClient.post(`/api/submissions/${submissionId}/request-deletion/`);
    await fetchRows();
  } catch (e) {
    alert(e?.response?.data?.detail || "Deletion request failed.");
  }
}

onMounted(fetchRows);

watch(selectedScope, () => {
  selectedSubmission.value = null;
  fetchRows();
});
</script>

<style scoped>
.submissions-page {
  padding: 1rem 0 2rem;
}

.scope-toggle-wrap {
  display: flex;
  justify-content: center;
  margin-top: 0.75rem;
}

.dashboard-card {
  border: 1px solid #dfe6ee;
  border-radius: 0.9rem;
}

.dashboard-card .card-header {
  background: #f8fafc;
  border-bottom: 1px solid #e4eaf1;
}

.compact-table-wrap {
  border: 1px solid #e4e9ef;
  border-radius: 0.5rem;
  overflow: hidden;
}

.compact-table {
  min-width: 980px;
  margin-bottom: 0;
}

.compact-table :deep(thead th) {
  border-bottom: 1px solid #dde6ef;
  color: inherit;
  font-weight: 600;
  font-size: 0.85rem;
}

.compact-table :deep(tbody td) {
  padding-top: 0.55rem;
  padding-bottom: 0.55rem;
  border-color: #edf1f5;
}

.compact-table :deep(tbody tr):hover {
  background: #fafcfe;
}

.sticky-header th {
  position: sticky;
  top: 0;
  z-index: 2;
  white-space: nowrap;
}

.metadata-cell {
  display: grid;
  gap: 0.2rem;
}

.metadata-line {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.metadata-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: inherit;
}

.institution-text {
  display: inline-block;
  max-width: 220px;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.created-date {
  font-weight: 500;
  line-height: 1.2;
}

.created-time {
  font-size: 0.82rem;
  color: #6c757d;
  line-height: 1.2;
}

.metadata-link {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.metadata-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.metadata-chip {
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  font-size: 0.74rem;
}

.actions-col {
  min-width: 240px;
}

.deletion-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 31px;
  padding: 0.25rem 0.6rem;
  line-height: 1.1;
}

.action-group .btn {
  border-radius: 0.5rem;
  font-weight: 600;
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.overlay-panel {
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.warning-modal {
  width: min(900px, 96vw);
  max-height: 85vh;
  padding: 1.1rem;
  overflow: auto;
}

.warning-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.9rem;
}

.side-drawer-wrap {
  justify-content: flex-end;
  padding-right: 0;
}

.side-drawer {
  width: min(620px, 96vw);
  height: 100vh;
  border-radius: 0;
  overflow-y: auto;
  padding: 1.1rem;
  border-left: 1px solid #dfe6ee;
  background: #fcfdff;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 0.75rem;
  margin-bottom: 0.85rem;
}

.drawer-section {
  border-bottom: 1px solid #f1f3f5;
  padding-bottom: 0.9rem;
  margin-bottom: 0.9rem;
}

@media (max-width: 767.98px) {
  .compact-table {
    min-width: 900px;
  }

  .warning-modal {
    width: 100%;
  }
}
</style>