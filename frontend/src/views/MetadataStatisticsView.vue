<template>
  <div class="container mt-5 text-dark">
    <h1 class="text-center mb-4">Statistics</h1>
    
    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading statistics...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Submission #{{ submissionId }}</h5>
        </div>
        <div class="card-body">
          <div class="row g-3 align-items-center">
            <div class="col-md-4">
              <p class="mb-0"><strong>Username:</strong> {{ statistics?.username || 'N/A' }}</p>
            </div>
            <div class="col-md-4">
              <p class="mb-0"><strong>Submission Type:</strong> {{ statistics?.submission_type || 'bacteria' }}</p>
            </div>
            <div class="col-md-4">
              <p class="mb-0"><strong>Created At:</strong> {{ formatDate(statistics?.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Sample Statistics</h5>
        </div>
        <div class="card-body">
          <div class="row g-3 justify-content-center">
            <div class="col-md-5">
              <div class="text-center p-3 border rounded">
                <h3 class="text-dark">{{ stats?.unique_sample_identifiers || 0 }}</h3>
                <p class="mb-0">Unique Sample IDs</p>
              </div>
            </div>
            <div class="col-md-5">
              <div class="text-center p-3 border rounded">
                <h3 class="text-dark">{{ stats?.unique_isolate_species_count || 0 }}</h3>
                <p class="mb-0">Unique Isolate Species</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Sequencing Platform Statistics</h5>
        </div>
        <div class="card-body">
          <div class="chart-wrap">
            <div ref="platformChartRef" class="plotly-chart"></div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Antibiotics Statistics</h5>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats?.antibiotics?.different_antibiotics_count || 0 }}</h4>
                <p class="mb-0">Different Antibiotics</p>
              </div>
            </div>
            <div class="col-md-6">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ (stats?.antibiotics?.sir_counts?.resistant || 0) + (stats?.antibiotics?.sir_counts?.intermediate || 0) + (stats?.antibiotics?.sir_counts?.susceptible || 0) }}</h4>
                <p class="mb-0">Antibiotic Test Records</p>
              </div>
            </div>
          </div>

          <template v-if="(statistics?.total_antibiotics_files || 0) > 0">
            <div class="chart-wrap mt-3">
              <div ref="sirChartRef" class="plotly-chart"></div>
            </div>
            <p class="chart-caption text-dark text-center mb-0">
              Distribution of antibiotic resistance outcomes
            </p>

            <div v-if="(stats?.antibiotics?.mic_numeric_count || 0) > 0" class="chart-wrap mt-4">
              <div ref="micChartRef" class="plotly-chart"></div>
            </div>
            <p v-if="(stats?.antibiotics?.mic_numeric_count || 0) > 0" class="chart-caption text-dark text-center mb-0">
              Distribution of MIC values
            </p>
          </template>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Submission Files Summary</h5>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ statistics?.total_fastq_files || 0 }}</h4>
                <p class="mb-0">FASTQ Files</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ statistics?.total_antibiotics_files || 0 }}</h4>
                <p class="mb-0">Antibiotics Files</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ statistics?.total_samples || 0 }}</h4>
                <p class="mb-0">FASTQ-linked Samples</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="text-center">
        <router-link to="/dashboard" class="btn btn-primary">
          Back to Dashboard
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useRoute } from "vue-router";
import * as PlotlyModule from "plotly.js-dist-min";
import apiClient from "../api/client";

const Plotly = PlotlyModule?.default || PlotlyModule;

const route = useRoute();
const submissionId = ref(route.params.submissionId);

const statistics = ref(null);
const stats = ref({});
const loading = ref(false);
const error = ref("");
const platformChartRef = ref(null);
const sirChartRef = ref(null);
const micChartRef = ref(null);

function renderPlatformChart() {
  if (!platformChartRef.value || !Plotly?.react) return;

  const labels = [
    "Single-end (R1)",
    "Paired-end (R1 + R2)",
    "Nanopore",
    "PacBio",
  ];

  const values = [
    stats.value?.illumina_r1_only_count || 0,
    stats.value?.illumina_r1_r2_count || 0,
    stats.value?.nanopore_count || 0,
    stats.value?.pacbio_count || 0,
  ];

  Plotly.react(
    platformChartRef.value,
    [
      {
        type: "bar",
        x: labels,
        y: values,
        text: values,
        textposition: "inside",
        insidetextanchor: "end",
        texttemplate: "%{y}",
        textfont: { color: "black", size: 12 },
      },
    ],
    {
      font: { color: "black" },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      margin: { t: 30, r: 20, b: 95, l: 78 },
      xaxis: {
        title: {
          text: "Sequencing Platform",
          standoff: 12,
          font: { color: "black", size: 14 },
        },
        tickangle: -20,
        automargin: true,
      },
      yaxis: {
        title: {
          text: "Number of Samples",
          standoff: 10,
          font: { color: "black", size: 14 },
        },
        rangemode: "tozero",
        automargin: true,
      },
    },
    { displayModeBar: false, responsive: true }
  );
}

function renderSirChart() {
  if (!sirChartRef.value || !Plotly?.react) return;

  const sirCounts = stats.value?.antibiotics?.sir_counts || {};
  const values = [
    sirCounts.resistant || 0,
    sirCounts.intermediate || 0,
    sirCounts.susceptible || 0,
  ];

  Plotly.react(
    sirChartRef.value,
    [
      {
        type: "pie",
        labels: ["Resistant", "Intermediate", "Susceptible"],
        values,
        textinfo: "label+percent",
        hoverinfo: "label+value+percent",
        textfont: { color: "black" },
      },
    ],
    {
      font: { color: "black" },
      margin: { t: 10, r: 10, b: 10, l: 10 },
      showlegend: true,
    },
    { displayModeBar: false, responsive: true }
  );
}

function renderMicChart() {
  if (!micChartRef.value || !Plotly?.react) return;

  const micValues = stats.value?.antibiotics?.mic_numeric_values || [];
  if (!Array.isArray(micValues) || micValues.length === 0) return;

  Plotly.react(
    micChartRef.value,
    [
      {
        type: "histogram",
        x: micValues,
        marker: { color: "#0d6efd" },
      },
    ],
    {
      font: { color: "black" },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      margin: { t: 20, r: 20, b: 75, l: 78 },
      xaxis: {
        title: {
          text: "MIC Value",
          standoff: 12,
          font: { color: "black", size: 14 },
        },
        automargin: true,
      },
      yaxis: {
        title: {
          text: "Frequency",
          standoff: 10,
          font: { color: "black", size: 14 },
        },
        rangemode: "tozero",
        automargin: true,
      },
      bargap: 0.08,
    },
    { displayModeBar: false, responsive: true }
  );
}

async function renderCharts() {
  await nextTick();
  renderPlatformChart();
  renderSirChart();
  renderMicChart();
}

function handleResize() {
  if (platformChartRef.value && Plotly?.Plots?.resize) {
    Plotly.Plots.resize(platformChartRef.value);
  }
  if (sirChartRef.value && Plotly?.Plots?.resize) {
    Plotly.Plots.resize(sirChartRef.value);
  }
  if (micChartRef.value && Plotly?.Plots?.resize) {
    Plotly.Plots.resize(micChartRef.value);
  }
}

function formatDate(iso) {
  if (!iso) return "N/A";
  const d = new Date(iso);
  return d.toLocaleString();
}

async function fetchStatistics() {
  loading.value = true;
  error.value = "";
  
  try {
    const res = await apiClient.get(`/api/submissions/${submissionId.value}/statistics/`);
    statistics.value = res.data;
    stats.value = res.data?.metadata_statistics || {};
    await renderCharts();
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load statistics.";
  } finally {
    loading.value = false;
    await nextTick();
    if (!error.value) {
      renderPlatformChart();
      renderSirChart();
      renderMicChart();
    }
  }
}

onMounted(() => {
  window.addEventListener("resize", handleResize);
  fetchStatistics();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  if (platformChartRef.value && Plotly?.purge) {
    Plotly.purge(platformChartRef.value);
  }
  if (sirChartRef.value && Plotly?.purge) {
    Plotly.purge(sirChartRef.value);
  }
  if (micChartRef.value && Plotly?.purge) {
    Plotly.purge(micChartRef.value);
  }
});
</script>

<style scoped>
.card {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-wrap {
  min-height: 340px;
}

.plotly-chart {
  width: 100%;
  height: 320px;
}

.chart-caption {
  font-size: 0.9rem;
}
</style>
