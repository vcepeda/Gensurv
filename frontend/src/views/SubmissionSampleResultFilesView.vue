<template>
  <div class="container-fluid py-3 result-browser-page">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
      <div>
        <h1 class="mb-1">Sample {{ sampleId }} Result Files</h1>
        <p class="text-muted mb-0">Submission {{ submissionId }}</p>
      </div>

      <!-- <RouterLink
        :to="{ name: 'submission_results', params: { submissionId } }"
        class="btn btn-outline-secondary btn-sm"
      >
        Back to Samples
      </RouterLink> -->
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="card h-100 shadow-sm">
      <div class="card-header">Results</div>
      <div class="card-body tree-panel">
        <div v-if="loadingTree" class="text-muted">Loading tree…</div>

        <ul v-else-if="tree.length" class="tree-root">
          <ResultTreeNode
            v-for="node in tree"
            :key="node.path"
            :node="node"
            @select-file="onSelectFile"
          />
        </ul>

        <div v-else class="text-muted">No files found in result folder.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "@/api/client";
import ResultTreeNode from "@/components/ResultTreeNode.vue";

const PREVIEWABLE_EXTENSIONS = new Set([".html", ".htm", ".csv", ".tsv", ".txt"]);

const route = useRoute();
const router = useRouter();
const submissionId = computed(() => Number(route.params.submissionId));
const sampleId = computed(() => String(route.params.sampleId || ""));

const loadingTree = ref(false);
const error = ref("");

const tree = ref([]);

function extensionOf(path) {
  const idx = path.lastIndexOf(".");
  return idx >= 0 ? path.slice(idx).toLowerCase() : "";
}

function fileEndpoint(path) {
  const params = new URLSearchParams({ path });
  return `/api/submissions/${submissionId.value}/samples/${encodeURIComponent(sampleId.value)}/result-file/?${params.toString()}`;
}

async function fetchTree() {
  loadingTree.value = true;
  error.value = "";

  try {
    const res = await apiClient.get(
      `/api/submissions/${submissionId.value}/samples/${encodeURIComponent(sampleId.value)}/result-files/`
    );
    tree.value = Array.isArray(res.data?.tree) ? res.data.tree : [];
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load result files.";
  } finally {
    loadingTree.value = false;
  }
}

async function onSelectFile(fileNode) {
  const path = fileNode?.path || "";
  if (!path) return;

  const ext = extensionOf(path);
  if (!PREVIEWABLE_EXTENSIONS.has(ext)) {
    window.location.href = fileEndpoint(path);
    return;
  }

  router.push({
    name: "submission_sample_result_file_view",
    params: {
      submissionId: submissionId.value,
      sampleId: sampleId.value,
    },
    query: { path },
  });
}

onMounted(fetchTree);
</script>

<style scoped>
.result-browser-page {
  min-height: 70vh;
}

.tree-panel {
  max-height: 72vh;
  overflow: auto;
}

.tree-root {
  margin: 0;
  padding: 0;
}
</style>
