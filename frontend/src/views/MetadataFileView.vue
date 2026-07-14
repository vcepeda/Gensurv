<template>
  <div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
      <h2 class="mb-0">{{ fileName || "Metadata File" }}</h2>
      <a v-if="fileUrl" :href="fileUrl" class="btn btn-primary btn-sm" download>
        Download
      </a>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="loading" class="text-muted">Loading file...</div>

    <div v-else-if="mode === 'table'" class="table-responsive border rounded">
      <table class="table table-sm table-striped table-hover align-middle mb-0">
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

    <pre v-else class="metadata-raw">{{ rawContent }}</pre>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";

const route = useRoute();

const fileUrl = computed(() => String(route.query.fileUrl || ""));
const fileName = computed(() => String(route.query.fileName || ""));

const loading = ref(false);
const error = ref("");
const mode = ref("none");
const rawContent = ref("");
const tableHeaders = ref([]);
const tableRows = ref([]);

function detectDelimiter(text) {
  const firstLine = String(text || "").split(/\r?\n/, 1)[0] || "";
  const commaCount = (firstLine.match(/,/g) || []).length;
  const tabCount = (firstLine.match(/\t/g) || []).length;
  const semicolonCount = (firstLine.match(/;/g) || []).length;

  if (tabCount >= commaCount && tabCount >= semicolonCount) return "\t";
  if (semicolonCount > commaCount) return ";";
  return ",";
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

async function fetchMetadataFile() {
  if (!fileUrl.value) {
    error.value = "Missing metadata file URL.";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const response = await apiClient.get(fileUrl.value, {
      responseType: "text",
      transformResponse: [(data) => data],
    });

    const content = String(response.data || "");
    rawContent.value = content;

    const delimiter = detectDelimiter(content);
    const tableData = buildTableData(content, delimiter);

    if (tableData.headers.length > 0) {
      tableHeaders.value = tableData.headers;
      tableRows.value = tableData.rows;
      mode.value = "table";
    } else {
      mode.value = "raw";
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load metadata file.";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchMetadataFile);
</script>

<style scoped>
.metadata-raw {
  white-space: pre-wrap;
  word-break: break-word;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.75rem;
}
</style>