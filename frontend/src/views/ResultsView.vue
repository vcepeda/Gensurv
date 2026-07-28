<template>
  <div class="container-fluid submissions-page">
    <div v-if="!authStore.isAuthenticated" class="text-center py-5">
      <h2>Login Required</h2>
      <p class="lead">
        To view results please <RouterLink to="/login">login</RouterLink> to your account.
      </p>
    </div>

    <template v-else>
      <div class="mb-4">
        <h1 class="text-center mb-2">Results</h1>
        <p class="lead text-center mb-2">
          Every submitted job, its service, and its pipeline status in one place.
        </p>

        <div class="scope-toggle-wrap">
          <div class="btn-group" role="group" aria-label="Results scope toggle">
            <input id="rscope-all" v-model="selectedScope" class="btn-check" type="radio" name="results-scope" value="all" autocomplete="off" />
            <label class="btn btn-outline-primary btn-sm" for="rscope-all">All submissions</label>

            <input id="rscope-mine" v-model="selectedScope" class="btn-check" type="radio" name="results-scope" value="mine" autocomplete="off" />
            <label class="btn btn-outline-primary btn-sm" for="rscope-mine">Your submissions</label>

            <input id="rscope-others" v-model="selectedScope" class="btn-check" type="radio" name="results-scope" value="others" autocomplete="off" />
            <label class="btn btn-outline-primary btn-sm" for="rscope-others">Other's submissions</label>
          </div>
        </div>
      </div>

      <div class="card shadow-sm dashboard-card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span class="fw-semibold">Jobs</span>
          <button class="btn btn-outline-secondary btn-sm" @click="fetchRows" :disabled="loading">Refresh</button>
        </div>

        <div class="card-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>

          <div v-if="!loading && rows.length === 0" class="text-center py-5">
            <h5 class="text-muted mb-0">
              {{ selectedScope === "others" ? "No other submissions available" : "No submissions available" }}
            </h5>
          </div>

          <div v-else class="table-responsive compact-table-wrap">
            <table class="table table-sm table-hover align-middle compact-table">
              <thead class="table-light sticky-header">
                <tr>
                  <th>Service</th>
                  <th>Owner</th>
                  <th>Submission</th>
                  <th>Submitted</th>
                  <th>Status</th>
                  <th>QC</th>
                  <th class="actions-col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in rows" :key="row.submission_id">
                  <td>
                    <span class="badge" :class="submissionTypeBadgeClass(row)">{{ submissionTypeLabel(row) }}</span>
                  </td>
                  <td class="text-nowrap">{{ row.username || "-" }}</td>
                  <td class="fw-semibold">#{{ row.submission_id }}</td>
                  <td>
                    <div class="created-date">{{ formatDateParts(row.created_at).date }}</div>
                    <div class="created-time">{{ formatDateParts(row.created_at).time }}</div>
                  </td>
                  <td>
                    <span class="badge" :class="statusBadgeClass(row)">{{ statusLabel(row) }}</span>
                  </td>
                  <td>
                    <RouterLink
                      v-if="row.qc?.total > 0"
                      :to="{ name: 'submission_results_dashboard', params: { submissionId: row.submission_id } }"
                      class="badge text-decoration-none"
                      :class="qcBadgeClass(row.qc)"
                      :title="row.qc.failed > 0 ? `${row.qc.failed} sample(s) failed QC` : 'All samples passed QC'"
                    >
                      {{ row.qc.succeeded }}/{{ row.qc.total }} passed
                    </RouterLink>
                    <span v-else class="text-muted">&mdash;</span>
                  </td>
                  <td>
                    <RouterLink
                      class="btn btn-primary btn-sm"
                      :class="{ disabled: !hasCompletedStatus(row) }"
                      :to="{ name: 'submission_results_dashboard', params: { submissionId: row.submission_id } }"
                      :aria-disabled="!hasCompletedStatus(row)"
                      :title="!hasCompletedStatus(row) ? 'Results not available yet' : 'View Results'"
                      @click="!hasCompletedStatus(row) && $event.preventDefault()"
                    >
                      View Results
                    </RouterLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="loading" class="text-muted">Loading…</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import apiClient from "@/api/client";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

const rows = ref([]);
const loading = ref(false);
const error = ref("");
const selectedScope = ref("all");

const SUBMISSION_TYPE_BADGES = {
  gensurv: { label: "Gensurv", class: "text-bg-success" },
  bacteria: { label: "Gensurv", class: "text-bg-success" },
  "num-sar_bacteria": { label: "NUM-SAR", class: "text-bg-info" },
  "num-sar_virus": { label: "NUM-SAR", class: "text-bg-primary" },
  cogdat: { label: "COGDAT", class: "text-bg-warning" },
};

function submissionTypeLabel(row) {
  return SUBMISSION_TYPE_BADGES[row.submission_type]?.label || row.submission_type || "Gensurv";
}

function submissionTypeBadgeClass(row) {
  return SUBMISSION_TYPE_BADGES[row.submission_type]?.class || "text-bg-success";
}

function formatDateParts(iso) {
  if (!iso) return { date: "", time: "" };
  const d = new Date(iso);
  return { date: d.toLocaleDateString(), time: d.toLocaleTimeString() };
}

function sampleStatuses(row) {
  return Object.values(row.analysis?.statuses || {});
}

function hasCompletedStatus(row) {
  return sampleStatuses(row).some((status) => status === "completed" || status === "finished");
}

function statusLabel(row) {
  const statuses = sampleStatuses(row);
  if (statuses.length === 0) return "Pending";
  const finishedCount = statuses.filter((s) => s === "finished" || s === "completed").length;
  if (finishedCount === statuses.length) return "Completed";
  if (finishedCount > 0) return "In Progress";
  return "Pending";
}

function statusBadgeClass(row) {
  const label = statusLabel(row);
  if (label === "Completed") return "text-bg-success";
  if (label === "In Progress") return "text-bg-info";
  return "text-bg-secondary";
}

function qcBadgeClass(qc) {
  if (!qc || qc.total === 0) return "text-bg-secondary";
  return qc.failed > 0 ? "text-bg-danger" : "text-bg-success";
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
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load results.";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchRows);
watch(selectedScope, fetchRows);
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
  min-width: 760px;
  margin-bottom: 0;
}

.compact-table :deep(thead th) {
  border-bottom: 1px solid #dde6ef;
  background: var(--num-slate);
  color: #ffffff;
  font-weight: 600;
  font-size: 0.85rem;
}

.compact-table :deep(tbody td) {
  padding-top: 0.55rem;
  padding-bottom: 0.55rem;
  border-color: #edf1f5;
}

.sticky-header th {
  position: sticky;
  top: 0;
  z-index: 2;
  white-space: nowrap;
  background: var(--num-slate);
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

.actions-col {
  min-width: 140px;
}
</style>
