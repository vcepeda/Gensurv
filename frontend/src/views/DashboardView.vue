<template>
  <div class="container-fluid">
    <div class="mb-5">
      <h1 class="text-center">Submissions</h1>
      <p class="lead">
        View uploaded data, including metadata, antibiotic files, FASTQ files, and their analysis statuses.
      </p>
    </div>

    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>Submission Details</span>
        <button class="btn btn-outline-secondary btn-sm" @click="fetchRows" :disabled="loading">
          Refresh
        </button>
      </div>

      <div class="card-body table-responsive">
        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <!-- Empty State -->
        <div v-if="!loading && rows.length === 0" class="text-center py-5">
          <h5 class="text-muted mb-3">You don't have any submissions</h5>
          <router-link to="/upload" class="btn btn-primary">
            Upload Data
          </router-link>
        </div>

        <table v-else class="table table-striped table-hover table-bordered">
          <thead class="thead-dark">
            <tr>
              <th>Username</th>
              <th>Submission ID</th>
              <th>Submission Date</th>
              <th>Metadata File</th>
              <th>Antibiotics Data</th>
              <th>FASTQ Files</th>
              <th>Analysis Status</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in rows" :key="row.submission_id">
              <td>{{ row.username }}</td>
              <td>{{ row.submission_id }}</td>
              <td>{{ formatDate(row.created_at) }}</td>

              <!-- Metadata -->
              <td>
                <div v-if="row.metadata?.files">
                  <div v-if="row.metadata.files.raw_url">
                    <strong>Raw:</strong>
                    <a :href="row.metadata.files.raw_url" target="_blank">{{ row.metadata.files.raw_name }}</a>
                  </div>
                  <div v-if="row.metadata.files.cleaned_url">
                    <strong>Cleaned:</strong>
                    <a :href="row.metadata.files.cleaned_url" target="_blank">{{ row.metadata.files.cleaned_name }}</a>
                  </div>
                </div>
                <span v-else class="text-muted">N/A</span>

                <div v-if="row.metadata?.resub_count" class="mt-1">
                  <small class="text-muted">🔁 Resubmissions: {{ row.metadata.resub_count }}</small>
                </div>

                <div v-if="row.metadata?.warnings" class="alert alert-warning mt-2 p-2">
                  <strong>Metadata Warning:</strong><br />
                  <pre class="mb-0" style="white-space: pre-wrap;">{{ row.metadata.warnings }}</pre>
                </div>

                <div class="mt-1" v-if="row.metadata?.can_resubmit">
                  <router-link
                    class="btn btn-warning btn-sm"
                    :to="{ name: 'resubmit', params: { submissionId: row.submission_id, fileType: 'metadata' } }"
                  >
                    Resubmit Metadata
                  </router-link>
                </div>

                <div class="mt-1">
                  <button
                    v-if="!row.deletion?.requested"
                    class="btn btn-danger btn-sm mt-2"
                    @click="requestDeletion(row.submission_id)"
                  >
                    Request Deletion
                  </button>
                  <div v-else class="alert alert-info mt-2 p-2">
                    Deletion has been requested for this submission.
                  </div>
                </div>
              </td>

              <!-- Antibiotics -->
              <td>
                <div v-if="hasAntibiotics(row)">
                  <div v-if="row.antibiotics?.files?.length">
                    <strong>Files:</strong><br />
                    <div v-for="f in row.antibiotics.files" :key="f.sample_id + (f.raw_url || '')" class="mb-2">
                      <strong>{{ f.sample_id }}</strong>:<br />
                      <div v-if="f.cleaned_url">
                        Raw:
                        <a :href="f.raw_url" target="_blank">{{ f.raw_name }}</a><br />
                        Cleaned:
                        <a :href="f.cleaned_url" target="_blank">{{ f.cleaned_name }}</a>
                      </div>
                      <div v-else>
                        <a :href="f.raw_url" target="_blank">{{ f.raw_name }}</a>
                      </div>
                    </div>
                  </div>

                  <div v-if="row.antibiotics?.info && Object.keys(row.antibiotics.info).length">
                    <strong>Info:</strong><br />
                    <div v-for="(info, sid) in row.antibiotics.info" :key="sid">
                      <strong>{{ sid }}</strong>: {{ info }}
                    </div>
                  </div>
                </div>
                <span v-else class="text-muted">N/A</span>

                <div v-if="row.antibiotics?.warnings" class="alert alert-warning mt-2 p-2">
                  <strong>Antibiotics Warning:</strong><br />
                  <pre class="mb-0" style="white-space: pre-wrap;">{{ row.antibiotics.warnings }}</pre>
                </div>
              </td>

              <!-- FASTQ -->
              <td>
                <div v-if="row.fastq?.grouped && Object.keys(row.fastq.grouped).length">
                  <div v-for="(files, sid) in row.fastq.grouped" :key="sid" class="mb-2">
                    <strong>{{ sid }}</strong>:<br />
                    <div v-for="f in files" :key="f.url">
                      <a :href="f.url" target="_blank">{{ f.name }}</a>
                    </div>
                  </div>
                </div>
                <span v-else class="text-muted">N/A</span>

                <div v-if="row.fastq?.extra_warning" class="alert alert-warning mt-2 p-2">
                  <strong>FASTQ Warning:</strong><br />
                  <pre class="mb-0" style="white-space: pre-wrap;">{{ row.fastq.extra_warning }}</pre>
                </div>
              </td>

              <!-- Analysis -->
              <td>
                <div v-if="row.analysis?.statuses && Object.keys(row.analysis.statuses).length">
                  <div v-for="(status, sid) in row.analysis.statuses" :key="sid" class="mb-1">
                    <strong>{{ sid }}</strong>:
                    <span class="badge" :class="badgeClass(status)">{{ status || "pending" }}</span>
                    <div v-if="status === 'completed'" class="mt-1">
                      <router-link
                        class="btn btn-sm btn-primary"
                        :to="{ name: 'sampleResults', params: { submissionId: row.submission_id, sampleId: sid } }"
                      >
                        View Results
                      </router-link>
                    </div>
                  </div>
                </div>
                <span v-else class="badge badge-warning">Pending</span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="loading" class="text-muted">Loading…</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import apiClient from "../api/client/"

const rows = ref([]);
const loading = ref(false);
const error = ref("");

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString();
}

function badgeClass(status) {
  console.log(status)
  if (status === "completed") return "badge text-bg-success";
  if (status === "failed") return "badge text-bg-danger";
  if (status === "pending") return "badge text-bg-warning";
  return "badge text-bg-warning";
}

function hasAntibiotics(row) {
  return (row.antibiotics?.files?.length || 0) > 0 || (row.antibiotics?.info && Object.keys(row.antibiotics.info).length);
}

async function fetchRows() {
  error.value = "";
  loading.value = true;
  try {
    const res = await apiClient.get("/api/dashboard/");
    rows.value = res.data;
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
</script>
