<template>
  <div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
      <div>
        <h1 class="mb-1">Submission {{ submissionId }} Results Dashboard</h1>
        <p class="lead mb-1">Explore each sample's pipeline status and results, from Bactopia's own QC summary.</p>
        <p class="mb-1">
          The analysis was done using
          <a href="https://bactopia.io/full-guide" target="_blank" rel="noopener noreferrer">bactopia.io</a>.
        </p>
        <ul class="qc-legend list-unstyled small text-muted mb-0">
          <li><span class="badge text-bg-warning">gold</span> Coverage &ge;100x, Quality &ge;Q30, Read length &ge;95bp, Contigs &lt;100</li>
          <li><span class="badge text-bg-light border">silver</span> Coverage &ge;50x, Quality &ge;Q20, Read length &ge;75bp, Contigs &lt;200</li>
          <li><span class="badge text-bg-secondary">bronze</span> Coverage &ge;20x, Quality &ge;Q12, Read length &ge;49bp, Contigs &lt;500</li>
          <li><span class="badge text-bg-danger">exclude</span> It failed to meet the bronze cutoffs or another rigorous quality control check. Please see the reason for exclusion next to the "exclude" label on the sample.</li>
        </ul>
        <details class="stage-legend small text-muted mt-1">
          <summary>What do Gather / QC / Assembler / ... mean?</summary>
          <ul class="list-unstyled mb-0 mt-1">
            <li v-for="stage in stageOrder" :key="stage">
              <strong>{{ stageLabel(stage) }}:</strong> {{ stageDescription(stage) }}
            </li>
          </ul>
        </details>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-else-if="loading" class="text-muted">Loading…</div>

    <template v-else>
      <div class="card mb-3 shadow-sm">
        <div class="card-body">
          <div class="row text-center g-3">
            <div class="col-6 col-md-3">
              <div class="fw-bold fs-4">{{ summary.total }}</div>
              <div class="text-muted">Total samples</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="fw-bold fs-4 text-success">{{ summary.succeeded }}</div>
              <div class="text-muted">Successful</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="fw-bold fs-4 text-danger">{{ summary.failed }}</div>
              <div class="text-muted">Failed</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="fw-bold fs-4 text-secondary">{{ summary.pending }}</div>
              <div class="text-muted">Pending</div>
            </div>
          </div>
        </div>
      </div>

      <div class="table-responsive">
        <table class="table table-bordered align-middle">
          <thead class="table-light">
            <tr>
              <th>Sample ID</th>
              <th>Species</th>
              <th>Sequencing Technology</th>
              <th v-for="stage in stageOrder" :key="stage">{{ stageLabel(stage) }}</th>
              <th>Status</th>
              <th>Tree</th>
              <th>Download</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sample in samples" :key="sample.sample_id">
              <td>
                <a :href="`/dashboard#submission-${submissionId}`" title="View submission in Dashboard">
                  {{ sample.sample_id }}
                </a>
              </td>
              <td>{{ sample.species || "—" }}</td>
              <td>{{ sample.sequencing_technology || "—" }}</td>
              <td v-for="stage in stageOrder" :key="stage" class="text-center" :class="{ 'merlin-cell': stage === 'merlin' }">
                <template v-if="stage === 'merlin' && sample.stages.merlin?.available">
                  <div class="d-flex align-items-center justify-content-center gap-1">
                    <RouterLink
                      :to="sampleResultsRoute(sample.sample_id, sample.stages.merlin.path)"
                      class="badge text-bg-light border text-dark text-decoration-none"
                      title="Jump to this stage's results"
                    >
                      Merlin
                    </RouterLink>
                    <button
                      class="btn btn-sm btn-link p-0 merlin-toggle"
                      type="button"
                      :aria-expanded="isMerlinExpanded(sample.sample_id) ? 'true' : 'false'"
                      title="Show tools run"
                      @click="toggleMerlin(sample.sample_id)"
                    >
                      {{ isMerlinExpanded(sample.sample_id) ? "▾" : "▸" }}
                    </button>
                  </div>
                  <div v-if="isMerlinExpanded(sample.sample_id)" class="merlin-tools small text-muted mt-1">
                    {{ sample.stages.merlin.tool }}
                  </div>
                </template>
                <template v-else-if="stage !== 'merlin'">
                  <RouterLink
                    v-if="sample.stages[stage]?.available"
                    :to="sampleResultsRoute(sample.sample_id, sample.stages[stage].path)"
                    class="badge text-bg-light border text-dark text-decoration-none"
                    title="Jump to this stage's results"
                  >
                    {{ sample.stages[stage].tool || "✓" }}
                  </RouterLink>
                  <span v-else class="text-muted">&mdash;</span>
                </template>
                <span v-else class="text-muted">&mdash;</span>
              </td>
              <td>
                <span
                  v-if="sample.rank"
                  class="badge"
                  :class="rankBadgeClass(sample.rank)"
                  :title="sample.reason || ''"
                >
                  {{ sample.rank }}
                </span>
                <span v-else class="badge text-bg-secondary">pending</span>
                <div v-if="sample.rank === 'exclude' && sample.reason" class="small text-danger mt-1">
                  {{ sample.reason }}
                </div>
              </td>
              <td class="text-center">
                <RouterLink
                  :to="sampleResultsRoute(sample.sample_id)"
                  title="Browse this sample's full result tree"
                >
                  <i class="fas fa-sitemap"></i>
                </RouterLink>
              </td>
              <td class="text-center">
                <a
                  v-if="sample.download?.available"
                  :href="downloadUrl(sample.sample_id, sample.download.filename)"
                  title="Download zipped results"
                >
                  <i class="fas fa-download"></i>
                </a>
                <span v-else class="text-muted small" :title="`Not generated yet: ${sample.download?.filename}`">
                  {{ sample.download?.filename }}
                </span>
              </td>
            </tr>
            <tr v-if="!samples.length">
              <td :colspan="stageOrder.length + 6" class="text-center text-muted">
                No samples found for this submission yet.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";

const STAGE_LABELS = {
  gather: "Gather",
  qc: "QC",
  assembler: "Assembler",
  annotator: "Annotator",
  sketcher: "Sketcher",
  mlst: "MLST",
  amrfinderplus: "AMRFinderPlus",
  merlin: "Merlin (Optional)",
};

const RANK_BADGE_CLASSES = {
  gold: "text-bg-warning",
  silver: "text-bg-light border",
  bronze: "text-bg-secondary",
  exclude: "text-bg-danger",
};

// Kept in sync with STAGE_DESCRIPTIONS in ResultTreeNode.vue
const STAGE_DESCRIPTIONS = {
  gather: "Collects all the raw sequencing data in one place, downloading samples from ENA/SRA or NCBI as needed.",
  qc: "Performs quality control on the raw reads, assessing and filtering out poor-quality data.",
  assembler: "Assembles the quality-controlled reads into contigs.",
  annotator: "Annotates the assembled contigs, identifying genes, proteins, rRNA, and tRNA.",
  sketcher: "Creates genomic sketches of the contigs and queries reference databases for rapid taxonomic classification.",
  mlst: "Determines the sequence type of the assembly by scanning it against PubMLST typing schemes.",
  amrfinderplus: "Identifies antibiotic resistance genes and mutations in the contigs and proteins.",
  merlin: "Automatically runs species-specific typing tools based on the sample's taxonomic classification. Depending on species, this can include: Kleborate, ClermonTyping, ECTyper, ShigaTyper, ShigEiFinder, ShigaPass, and STECFinder.",
};

const route = useRoute();
const submissionId = computed(() => Number(route.params.submissionId));

const loading = ref(false);
const error = ref("");
const stageOrder = ref([]);
const samples = ref([]);
const summary = ref({ total: 0, succeeded: 0, failed: 0, pending: 0 });
const expandedMerlin = ref({});

function isMerlinExpanded(sampleId) {
  return !!expandedMerlin.value[sampleId];
}

function toggleMerlin(sampleId) {
  expandedMerlin.value = {
    ...expandedMerlin.value,
    [sampleId]: !expandedMerlin.value[sampleId],
  };
}

function stageLabel(stage) {
  return STAGE_LABELS[stage] || stage;
}

function stageDescription(stage) {
  return STAGE_DESCRIPTIONS[stage] || "";
}

function rankBadgeClass(rank) {
  return RANK_BADGE_CLASSES[rank] || "text-bg-secondary";
}

function sampleResultsRoute(sampleId, highlightPath) {
  return {
    name: "submission_sample_result_files",
    params: { submissionId: submissionId.value, sampleId },
    query: highlightPath ? { highlight: highlightPath } : undefined,
  };
}

function downloadUrl(sampleId, filename) {
  const params = new URLSearchParams({ path: filename });
  return `/api/submissions/${submissionId.value}/samples/${encodeURIComponent(sampleId)}/result-file/?${params.toString()}`;
}

async function fetchDashboard() {
  loading.value = true;
  error.value = "";

  try {
    const res = await apiClient.get(`/api/submissions/${submissionId.value}/results/dashboard/`);
    stageOrder.value = res.data?.stage_order || [];
    samples.value = res.data?.samples || [];
    summary.value = {
      total: res.data?.total || 0,
      succeeded: res.data?.succeeded || 0,
      failed: res.data?.failed || 0,
      pending: res.data?.pending || 0,
    };
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load results dashboard.";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDashboard);
</script>

<style scoped>
.qc-legend li {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.15rem;
}

.merlin-cell {
  max-width: 140px;
}

.merlin-toggle {
  text-decoration: none;
  line-height: 1;
}

.merlin-tools {
  max-width: 220px;
  white-space: normal;
  word-break: break-word;
  margin-left: auto;
  margin-right: auto;
}

.stage-legend summary {
  cursor: pointer;
  color: #0d6efd;
}

.stage-legend li {
  margin-bottom: 0.15rem;
}
</style>
