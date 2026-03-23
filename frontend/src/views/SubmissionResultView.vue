<template>
  <div class="container-fluid">
    <h1>Submission {{ submissionId }} Results</h1>
    <p class="lead">Explore the results for the samples in this submission.</p>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="card mb-4">
      <div class="card-header">Samples in Submission {{ submissionId }}</div>

      <div class="card-body">
        <div v-if="loading">Loading…</div>

        <ul v-else class="list-group">
          <li
            v-for="sid in sampleIds"
            :key="sid"
            class="list-group-item d-flex justify-content-between align-items-center"
          >
            <RouterLink
              :to="{ name: 'sample_results', params: { submissionId, sampleId: sid } }"
              class="text-decoration-none"
            >
              Sample {{ sid }}
            </RouterLink>

            <span class="badge bg-primary rounded-pill">View Results</span>
          </li>

          <li v-if="!loading && sampleIds.length === 0" class="list-group-item">
            No samples found for this submission yet.
          </li>
        </ul>
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">FASTQ Files</div>
      <div class="card-body">
        <ul class="list-group">
          <li
            v-for="(file, idx) in fastqFiles"
            :key="`fastq-${idx}-${file.name}`"
            class="list-group-item d-flex justify-content-between align-items-center"
          >
            <a href="#" @click.prevent>{{ file.name }}</a>
            <span v-if="file.sample_id" class="text-muted small">{{ file.sample_id }}</span>
          </li>
          <li v-if="!loading && fastqFiles.length === 0" class="list-group-item text-muted">
            No FASTQ files found for this submission.
          </li>
        </ul>
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">Antibiotics Files</div>
      <div class="card-body">
        <ul class="list-group">
          <li
            v-for="(file, idx) in antibioticsFiles"
            :key="`antibiotics-${idx}-${file.name}`"
            class="list-group-item d-flex justify-content-between align-items-center"
          >
            <a href="#" @click.prevent>{{ file.name }}</a>
            <span v-if="file.sample_id" class="text-muted small">{{ file.sample_id }}</span>
          </li>
          <li v-if="!loading && antibioticsFiles.length === 0" class="list-group-item text-muted">
            No antibiotics files found for this submission.
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";

const route = useRoute();
const submissionId = computed(() => Number(route.params.submissionId));

const loading = ref(false);
const error = ref("");
const sampleIds = ref([]);
const fastqFiles = ref([]);
const antibioticsFiles = ref([]);

async function fetchSamples() {
  loading.value = true;
  error.value = "";

  try {
    const res = await apiClient.get(`/api/submissions/${submissionId.value}/samples/`);
    sampleIds.value = res.data?.sample_ids || [];
    fastqFiles.value = res.data?.fastq_files || [];
    antibioticsFiles.value = res.data?.antibiotics_files || [];
  } catch (e) {
    error.value =
      e?.response?.data?.detail ||
      "Failed to load samples for this submission.";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchSamples);
</script>
