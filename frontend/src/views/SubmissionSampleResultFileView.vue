<template>
  <div class="file-view-page">
    <template v-if="mode === 'html'">
      <iframe :srcdoc="content" class="preview-iframe" title="HTML Preview"></iframe>
    </template>

    <template v-else-if="mode === 'table'">
      <div class="table-responsive preview-table-wrap">
        <table class="table table-sm table-striped table-hover align-middle preview-table">
          <thead class="table-light sticky-top">
            <tr>
              <th v-for="header in tableHeaders" :key="header">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in tableRows" :key="rowIndex">
              <td v-for="header in tableHeaders" :key="header">{{ row[header] ?? "" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <template v-else-if="mode === 'text'">
      <pre class="preview-text">{{ content }}</pre>
    </template>

    <pre v-else class="preview-text">{{ content || error }}</pre>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";

const route = useRoute();

const submissionId = computed(() => Number(route.params.submissionId));
const sampleId = computed(() => String(route.params.sampleId || ""));
const filePath = computed(() => String(route.query.path || ""));

const loading = ref(false);
const error = ref("");
const content = ref("");
const mode = ref("none");
const tableHeaders = ref([]);
const tableRows = ref([]);

function extensionOf(path) {
  const idx = path.lastIndexOf(".");
  return idx >= 0 ? path.slice(idx).toLowerCase() : "";
}

function parseDelimitedText(rawText, delimiter) {
  const rows = [];
  let currentRow = [];
  let currentCell = "";
  let inQuotes = false;

  for (let index = 0; index < rawText.length; index += 1) {
    const char = rawText[index];
    const nextChar = rawText[index + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        currentCell += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (!inQuotes && char === delimiter) {
      currentRow.push(currentCell);
      currentCell = "";
      continue;
    }

    if (!inQuotes && (char === "\n" || char === "\r")) {
      if (char === "\r" && nextChar === "\n") {
        index += 1;
      }
      currentRow.push(currentCell);
      rows.push(currentRow);
      currentRow = [];
      currentCell = "";
      continue;
    }

    currentCell += char;
  }

  currentRow.push(currentCell);
  rows.push(currentRow);

  return rows.filter((row) => row.some((cell) => String(cell).trim() !== ""));
}

function buildTableData(rawText, delimiter) {
  const parsedRows = parseDelimitedText(rawText, delimiter);
  if (!parsedRows.length) {
    return { headers: [], rows: [] };
  }

  const headers = parsedRows[0].map((header, headerIndex) => {
    const label = String(header || "").trim();
    return label || `Column ${headerIndex + 1}`;
  });

  const rows = parsedRows.slice(1).map((row) => {
    const normalized = {};
    headers.forEach((header, headerIndex) => {
      normalized[header] = row[headerIndex] ?? "";
    });
    return normalized;
  });

  return { headers, rows };
}

function fileEndpoint(path) {
  const params = new URLSearchParams({ path });
  return `/api/submissions/${submissionId.value}/samples/${encodeURIComponent(sampleId.value)}/result-file/?${params.toString()}`;
}

async function fetchFile() {
  const path = filePath.value;
  if (!path) {
    error.value = "Missing file path.";
    mode.value = "none";
    content.value = "";
    return;
  }

  loading.value = true;
  error.value = "";
  content.value = "";
  mode.value = "none";
  tableHeaders.value = [];
  tableRows.value = [];

  try {
    const res = await apiClient.get(fileEndpoint(path));
    const payload = res.data || {};
    content.value = String(payload.content || "");
    const ext = extensionOf(path);
    if (ext === ".html" || ext === ".htm") {
      mode.value = "html";
    } else if (ext === ".csv" || ext === ".tsv") {
      const delimiter = ext === ".tsv" ? "\t" : ",";
      const tableData = buildTableData(content.value, delimiter);
      if (tableData.headers.length > 0) {
        tableHeaders.value = tableData.headers;
        tableRows.value = tableData.rows;
        mode.value = "table";
      } else {
        mode.value = "text";
      }
    } else {
      mode.value = "text";
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load file preview.";
    content.value = "";
    mode.value = "text";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchFile);
watch(() => route.query.path, fetchFile);
</script>

<style scoped>
.file-view-page {
  min-height: 100vh;
  width: 100vw;
  padding: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.preview-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.preview-iframe {
  width: 100%;
  height: 100vh;
  flex: 1;
  min-height: 0;
  border: 0;
  background: #fff;
}

.preview-table {
  font-size: 0.9rem;
  width: max-content;
  min-width: 100%;
}

.preview-text {
  flex: 1;
  min-height: 0;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9rem;
  background: #fff;
  border: 0;
  padding: 1rem;
  overflow: auto;
}
</style>