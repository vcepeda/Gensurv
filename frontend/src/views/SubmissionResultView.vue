<template>
  <div class="container-fluid">
    <h1>Submission {{ submissionId }} Results</h1>
    <p class="lead">Explore the results for the samples in this submission.</p>
    <p>
      The analysis was done using
      <a href="https://bactopia.io/full-guide" target="_blank" rel="noopener noreferrer">bactopia.io</a>.
    </p>

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
            <span>Sample {{ sid }}</span>

            <RouterLink
              class="badge bg-primary rounded-pill text-decoration-none"
              :to="{
                name: 'submission_sample_result_files',
                params: { submissionId, sampleId: sid },
              }"
            >
              View Results
            </RouterLink>
          </li>

          <li v-if="!loading && sampleIds.length === 0" class="list-group-item">
            No samples found for this submission yet.
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

async function fetchSamples() {
  loading.value = true;
  error.value = "";

  try {
    const res = await apiClient.get(`/api/submissions/${submissionId.value}/samples/`);
    sampleIds.value = res.data?.sample_ids || [];
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
