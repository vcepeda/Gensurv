<template>
  <div class="container mt-5 text-dark">
    <h1 class="text-center mb-4">Statistics</h1>

    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading global statistics...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Overview</h5>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats.total_submissions || 0 }}</h4>
                <p class="mb-0">Total Submissions</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats.total_unique_sample_identifiers || 0 }}</h4>
                <p class="mb-0">Unique Sample Identifiers</p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats.total_unique_isolate_species || 0 }}</h4>
                <p class="mb-0">Unique Isolate Species</p>
              </div>
            </div>
          </div>
          <div class="row g-3 mt-1 justify-content-center">
            <div class="col-md-5">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats.total_fastq_files || 0 }}</h4>
                <p class="mb-0">Total FASTQ Files</p>
              </div>
            </div>
            <div class="col-md-5">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ stats.total_antibiotics_files || 0 }}</h4>
                <p class="mb-0">Total Antibiotics Files</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">QC Pass/Fail Overview</h5>
        </div>
        <div class="card-body">
          <div class="row g-3 text-center mb-2">
            <div class="col-6 col-md-3">
              <div class="p-2">
                <h3 class="mb-0">{{ qcPassRate === null ? "-" : `${qcPassRate}%` }}</h3>
                <p class="mb-0 text-muted">Passed</p>
              </div>
            </div>
          </div>
          <div class="row g-3">
            <div class="col-6 col-md-3">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ qcRankCounts.gold || 0 }}</h4>
                <p class="mb-0">Gold</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ qcRankCounts.silver || 0 }}</h4>
                <p class="mb-0">Silver</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ qcRankCounts.bronze || 0 }}</h4>
                <p class="mb-0">Bronze</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-center p-3 border rounded">
                <h4 class="text-dark">{{ qcRankCounts.exclude || 0 }}</h4>
                <p class="mb-0">Excluded</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Sequencing Platform Distribution</h5>
        </div>
        <div class="card-body">
          <div class="chart-wrap">
            <div ref="platformChartRef" class="plotly-chart"></div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Antibiotics SIR Distribution</h5>
        </div>
        <div class="card-body">
          <div class="chart-wrap">
            <div ref="sirChartRef" class="plotly-chart"></div>
          </div>
        </div>
      </div>

      <div class="card mb-4" v-if="micValues.length > 0">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Antibiotics MIC Distribution</h5>
        </div>
        <div class="card-body">
          <div class="chart-wrap">
            <div ref="micChartRef" class="plotly-chart"></div>
          </div>
        </div>
      </div>

      <div class="card mb-4" v-if="germanyTotalCount > 0">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Data Origin</h5>
        </div>
        <div class="card-body">
          <div class="chart-wrap">
            <div ref="mapContainerRef" class="leaflet-map"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as PlotlyModule from "plotly.js-dist-min";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import bundeslaenderGeoJson from "../assets/bundeslaender.geo.json";
import apiClient from "../api/client";

const Plotly = PlotlyModule?.default || PlotlyModule;

const loading = ref(false);
const error = ref("");
const stats = ref({});

const platformChartRef = ref(null);
const sirChartRef = ref(null);
const micChartRef = ref(null);
const mapContainerRef = ref(null);

const micValues = ref([]);
const germanyTotalCount = ref(0);
const germanyLocations = ref([]);

const qcRankCounts = computed(() => stats.value?.qc_rank_counts || {});
const qcPassRate = computed(() => {
  const c = qcRankCounts.value;
  const total = (c.gold || 0) + (c.silver || 0) + (c.bronze || 0) + (c.exclude || 0);
  if (total === 0) return null;
  return Math.round((((c.gold || 0) + (c.silver || 0) + (c.bronze || 0)) / total) * 1000) / 10;
});

let germanyMap = null;
let germanyMarkersLayer = null;
let germanyStatesLayer = null;
const germanyBounds = [
  [47.2, 5.5],
  [55.2, 15.6],
];

const germanStateCentroids = {
  badenwuerttemberg: { lat: 48.6616, lon: 9.3501 },
  badenwurttemberg: { lat: 48.6616, lon: 9.3501 },
  bayern: { lat: 48.7904, lon: 11.4979 },
  berlin: { lat: 52.52, lon: 13.405 },
  brandenburg: { lat: 52.4125, lon: 12.5316 },
  bremen: { lat: 53.0793, lon: 8.8017 },
  hamburg: { lat: 53.5511, lon: 9.9937 },
  hessen: { lat: 50.6521, lon: 9.1624 },
  mecklenburgvorpommern: { lat: 53.6127, lon: 12.4296 },
  niedersachsen: { lat: 52.6367, lon: 9.8451 },
  nordrheinwestfalen: { lat: 51.4332, lon: 7.6616 },
  rheinlandpfalz: { lat: 49.9929, lon: 7.8467 },
  saarland: { lat: 49.3964, lon: 7.023 },
  sachsen: { lat: 51.1045, lon: 13.2017 },
  sachsenanhalt: { lat: 51.95, lon: 11.6923 },
  schleswigholstein: { lat: 54.2194, lon: 9.6961 },
  thueringen: { lat: 50.9848, lon: 11.0299 },
  thuringen: { lat: 50.9848, lon: 11.0299 },
};

function formatDate(iso) {
  if (!iso) return "N/A";
  const d = new Date(iso);
  return d.toLocaleString();
}

function renderPlatformChart() {
  if (!platformChartRef.value || !Plotly?.react) return;
  const platform = stats.value?.platform_counts || {};
  const labels = ["Single-end (R1)", "Paired-end (R1 + R2)", "Nanopore", "PacBio"];
  const values = [
    platform.illumina_r1_only || 0,
    platform.illumina_r1_r2 || 0,
    platform.nanopore || 0,
    platform.pacbio || 0,
  ];

  Plotly.react(
    platformChartRef.value,
    [{ type: "bar", x: labels, y: values, text: values, textposition: "inside", insidetextanchor: "end", texttemplate: "%{y}", textfont: { color: "black", size: 12 } }],
    {
      font: { color: "black" },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      margin: { t: 30, r: 20, b: 95, l: 78 },
      xaxis: {
        title: { text: "Sequencing Platform", standoff: 12, font: { color: "black", size: 14 } },
        tickangle: -20,
        automargin: true,
      },
      yaxis: {
        title: { text: "Count", standoff: 10, font: { color: "black", size: 14 } },
        rangemode: "tozero",
        automargin: true,
      },
    },
    { displayModeBar: false, responsive: true }
  );
}

function renderSirChart() {
  if (!sirChartRef.value || !Plotly?.react) return;
  const sir = stats.value?.sir_counts || {};
  const values = [sir.resistant || 0, sir.intermediate || 0, sir.susceptible || 0];

  Plotly.react(
    sirChartRef.value,
    [{ type: "pie", labels: ["Resistant", "Intermediate", "Susceptible"], values, textinfo: "label+percent", hoverinfo: "label+value+percent", textfont: { color: "black" } }],
    { font: { color: "black" }, margin: { t: 10, r: 10, b: 10, l: 10 }, showlegend: true },
    { displayModeBar: false, responsive: true }
  );
}

function renderMicChart() {
  if (!micChartRef.value || !Plotly?.react || micValues.value.length === 0) return;

  Plotly.react(
    micChartRef.value,
    [{ type: "histogram", x: micValues.value, marker: { color: "#0d6efd" } }],
    {
      font: { color: "black" },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      margin: { t: 20, r: 20, b: 75, l: 78 },
      xaxis: {
        title: { text: "MIC Value", standoff: 12, font: { color: "black", size: 14 } },
        automargin: true,
      },
      yaxis: {
        title: { text: "Frequency", standoff: 10, font: { color: "black", size: 14 } },
        rangemode: "tozero",
        automargin: true,
      },
      bargap: 0.08,
    },
    { displayModeBar: false, responsive: true }
  );
}

function normalizeCountry(value) {
  const country = (value || "").trim().toLowerCase();
  return country;
}

function isGermanyCountry(value) {
  const normalized = normalizeCountry(value);
  return ["germany", "deutschland", "de", "german", "deu", "ger"].includes(normalized);
}

function buildGermanyLocationKey(row) {
  return [row.city || "", row.postal_code || "", row.state || "", "Germany"].join("|");
}

function normalizeStateKey(value) {
  return (value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ä/g, "ae")
    .replace(/ö/g, "oe")
    .replace(/ü/g, "ue")
    .replace(/ß/g, "ss")
    .replace(/[^a-z]/g, "");
}

function fallbackPointFromState(row) {
  const key = normalizeStateKey(row?.state || "");
  return germanStateCentroids[key] || null;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function hashString(input) {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function estimatePointFromRow(row) {
  const base = fallbackPointFromState(row) || { lat: 51.1657, lon: 10.4515 };
  const key = buildGermanyLocationKey(row);
  const hashA = hashString(key);
  const hashB = hashString(`${key}#b`);

  const factor = 0.35 + (hashA % 100) / 160;

  const hasStateBase = Boolean(fallbackPointFromState(row));
  const latRadius = hasStateBase ? 0.18 : 0.55;
  const lonRadius = hasStateBase ? 0.28 : 0.75;
  const angle = ((hashA % 360) * Math.PI) / 180;

  const lat = clamp(base.lat + Math.cos(angle) * latRadius * factor, germanyBounds[0][0], germanyBounds[1][0]);
  const lon = clamp(base.lon + Math.sin(angle + (hashB % 45) / 180) * lonRadius * factor, germanyBounds[0][1], germanyBounds[1][1]);

  return { lat, lon };
}

function normalizeLocationPart(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const lowered = text.toLowerCase();
  if (["0", "00", "000", "0000", "na", "n/a", "none", "null", "unknown", "-"].includes(lowered)) {
    return "";
  }
  return text;
}

const STATE_FILL_WITH_DATA = "#ffffff";
const STATE_FILL_NO_DATA = "#f0f0f0";
const STATE_FILL_HOVER = "#e4e8ec";
const STATE_BORDER = "#c6cbd1";

// Maps the many spellings that show up in uploaded metadata (umlaut vs. "ue",
// English names, common abbreviations) onto the ISO codes the GeoJSON uses.
// Note that normalizeStateKey strips umlauts rather than expanding them, so
// "Thüringen" normalizes to "thuringen" while "Thueringen" stays "thueringen" -
// both spellings need an entry here.
const STATE_ALIAS_TO_ISO = {
  badenwuerttemberg: "DE-BW", badenwurttemberg: "DE-BW", bw: "DE-BW",
  bayern: "DE-BY", bavaria: "DE-BY", by: "DE-BY",
  berlin: "DE-BE", be: "DE-BE",
  brandenburg: "DE-BB", bb: "DE-BB",
  bremen: "DE-HB", hb: "DE-HB",
  hamburg: "DE-HH", hh: "DE-HH",
  hessen: "DE-HE", hesse: "DE-HE", he: "DE-HE",
  mecklenburgvorpommern: "DE-MV", mv: "DE-MV",
  niedersachsen: "DE-NI", lowersaxony: "DE-NI", ni: "DE-NI",
  nordrheinwestfalen: "DE-NW", northrhinewestphalia: "DE-NW", nrw: "DE-NW", nw: "DE-NW",
  rheinlandpfalz: "DE-RP", rhinelandpalatinate: "DE-RP", rp: "DE-RP",
  saarland: "DE-SL", sl: "DE-SL",
  sachsen: "DE-SN", saxony: "DE-SN", sn: "DE-SN",
  sachsenanhalt: "DE-ST", saxonyanhalt: "DE-ST", st: "DE-ST",
  schleswigholstein: "DE-SH", sh: "DE-SH",
  thueringen: "DE-TH", thuringen: "DE-TH", thuringia: "DE-TH", th: "DE-TH",
};

function stateIsoFromValue(value) {
  return STATE_ALIAS_TO_ISO[normalizeStateKey(value)] || null;
}

function statesWithData() {
  const codes = new Set();
  for (const row of germanyLocations.value) {
    const iso = stateIsoFromValue(row?.state || "");
    if (iso) codes.add(iso);
  }
  return codes;
}

function stateStyle(feature, dataCodes) {
  const iso = feature?.properties?.id || "";
  return {
    fillColor: dataCodes.has(iso) ? STATE_FILL_WITH_DATA : STATE_FILL_NO_DATA,
    fillOpacity: 1,
    color: STATE_BORDER,
    weight: 1.2,
  };
}

// Small states get a smaller label so the text doesn't overrun the shape.
const SMALL_STATE_ISO_CODES = new Set(["DE-HB", "DE-HH", "DE-BE", "DE-SL"]);

function bindStateNameLabel(feature, layer) {
  const name = feature?.properties?.name;
  if (!name) return;
  const sizeClass = SMALL_STATE_ISO_CODES.has(feature?.properties?.id)
    ? "state-name-label--small"
    : "";
  // Not permanent: Leaflet shows/hides this automatically on the layer's own
  // mouseover/mouseout. Pins sit in a separate, higher pane, so hovering a
  // pin never fires the polygon's mouseover - the state label stays hidden
  // and only the pin's own tooltip shows.
  layer.bindTooltip(name, {
    direction: "center",
    className: `state-name-label ${sizeClass}`.trim(),
    interactive: false,
  });
}

function ensureGermanyMap() {
  if (germanyMap || !mapContainerRef.value) return;
  germanyMap = L.map(mapContainerRef.value, {
    center: [51.1657, 10.4515],
    zoom: 6,
    minZoom: 5,
    maxZoom: 10,
    maxBounds: germanyBounds,
    maxBoundsViscosity: 1.0,
    worldCopyJump: false,
    zoomSnap: 0.25,
    zoomControl: false,
    attributionControl: false,
  });

  L.control.zoom({ position: "bottomleft" }).addTo(germanyMap);

  // No tile basemap on purpose - the Bundesland outlines are the whole map.
  germanyStatesLayer = L.geoJSON(bundeslaenderGeoJson, {
    style: (feature) => stateStyle(feature, statesWithData()),
    onEachFeature: (feature, layer) => {
      bindStateNameLabel(feature, layer);
      layer.on({
        mouseover: () => layer.setStyle({ fillColor: STATE_FILL_HOVER }),
        mouseout: () => layer.setStyle(stateStyle(feature, statesWithData())),
        click: (event) => {
          // Keep the map-level click (which resets the view) from also firing.
          L.DomEvent.stopPropagation(event);
          germanyMap.fitBounds(layer.getBounds(), { padding: [24, 24] });
        },
      });
    },
  }).addTo(germanyMap);

  // Clicking empty space zooms back out to the whole country.
  germanyMap.on("click", () => resetGermanyMapView());

  germanyMarkersLayer = L.layerGroup().addTo(germanyMap);
}

function resetGermanyMapView() {
  if (!germanyMap || !germanyStatesLayer) return;
  germanyMap.fitBounds(germanyStatesLayer.getBounds(), { padding: [16, 16] });
}

function refreshStateStyles() {
  if (!germanyStatesLayer) return;
  const dataKeys = statesWithData();
  germanyStatesLayer.eachLayer((layer) => {
    layer.setStyle(stateStyle(layer.feature, dataKeys));
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function markerSize(count) {
  return Math.max(26, Math.min(44, 22 + Math.round(Math.log10((count || 1) + 1) * 10)));
}

function markerIcon(count) {
  const size = markerSize(count);
  return L.divIcon({
    html: `<span class="pin-drop" style="width:${size}px;height:${size}px;"></span>`,
    className: "germany-pin-marker",
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size + 4],
    tooltipAnchor: [0, -size + 4],
  });
}

function spreadPointIfOverlapping(point, placedPoints) {
  const nearThreshold = 0.05;
  const neighbors = placedPoints.filter(
    (p) => Math.abs(p.lat - point.lat) < nearThreshold && Math.abs(p.lon - point.lon) < nearThreshold
  );

  if (neighbors.length === 0) {
    return point;
  }

  const idx = neighbors.length;
  const ring = Math.floor(idx / 8);
  const posInRing = idx % 8;
  const angle = (2 * Math.PI * posInRing) / 8;
  const radius = 0.015 + ring * 0.012;

  const spread = {
    lat: clamp(point.lat + Math.cos(angle) * radius, germanyBounds[0][0], germanyBounds[1][0]),
    lon: clamp(point.lon + Math.sin(angle) * radius, germanyBounds[0][1], germanyBounds[1][1]),
  };

  return spread;
}

async function renderGermanyMap() {
  if (!mapContainerRef.value || germanyLocations.value.length === 0) return;

  ensureGermanyMap();
  if (!germanyMap || !germanyMarkersLayer) return;

  germanyMarkersLayer.clearLayers();
  const bounds = [];
  const placedPoints = [];

  for (const row of germanyLocations.value) {
    const basePoint = estimatePointFromRow(row);
    if (!basePoint) continue;
    const point = spreadPointIfOverlapping(basePoint, placedPoints);
    placedPoints.push(point);

    const marker = L.marker([point.lat, point.lon], {
      icon: markerIcon(row.count),
      riseOnHover: true,
    });
    const locationLabel = [row.city, row.state].filter(Boolean).join(", ");
    const sampleLabel = `${row.count} sample${row.count === 1 ? "" : "s"}`;
    marker.bindTooltip(
      `<strong>${escapeHtml(locationLabel || "Germany")}</strong><br/>${sampleLabel}`,
      { direction: "top", opacity: 1 }
    );
    marker.on("click", (event) => L.DomEvent.stopPropagation(event));
    marker.addTo(germanyMarkersLayer);
    bounds.push([point.lat, point.lon]);
  }

  refreshStateStyles();

  if (germanyStatesLayer) {
    germanyMap.fitBounds(germanyStatesLayer.getBounds(), { padding: [16, 16] });
  } else if (bounds.length > 0) {
    germanyMap.fitBounds(bounds, { padding: [30, 30], maxZoom: 8 });
  } else {
    germanyMap.setView([51.1657, 10.4515], 6);
  }

  germanyMap.setMaxBounds(germanyBounds);

  setTimeout(() => {
    if (germanyMap) germanyMap.invalidateSize();
  }, 0);
}

async function renderCharts() {
  await nextTick();
  renderPlatformChart();
  renderSirChart();
  renderMicChart();
  await renderGermanyMap();
}

function handleResize() {
  [platformChartRef.value, sirChartRef.value, micChartRef.value].forEach((chartEl) => {
    if (chartEl && Plotly?.Plots?.resize) {
      Plotly.Plots.resize(chartEl);
    }
  });
  if (germanyMap) germanyMap.invalidateSize();
}

async function fetchGlobalStatistics() {
  loading.value = true;
  error.value = "";
  try {
    const res = await apiClient.get("/api/statistics/global/");
    stats.value = res.data || {};

    const values = Array.isArray(stats.value?.mic_numeric_values) ? stats.value.mic_numeric_values : [];
    micValues.value = values.filter((value) => Number.isFinite(Number(value))).map((value) => Number(value));

    const mapRows = Array.isArray(stats.value?.map_location_counts) ? stats.value.map_location_counts : [];
    const cityAggregate = new Map();
    let germanyCount = 0;
    mapRows.forEach((row) => {
      const countryRaw = normalizeCountry(row?.country);
      const count = Number(row?.count || 0);
      if (!Number.isFinite(count) || count <= 0) return;
      if (isGermanyCountry(countryRaw)) {
        germanyCount += count;
        const city = normalizeLocationPart(row?.city);
        const state = normalizeLocationPart(row?.state);
        if (!city) return;

        const key = `${city.toLowerCase()}|${state.toLowerCase()}`;
        if (!cityAggregate.has(key)) {
          cityAggregate.set(key, {
            city,
            postal_code: "",
            state,
            country: row?.country || "",
            count: 0,
          });
        }
        cityAggregate.get(key).count += count;
      }
    });

    germanyLocations.value = Array.from(cityAggregate.values()).sort((a, b) => b.count - a.count);
    germanyTotalCount.value = germanyCount;

    await renderCharts();
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load global statistics.";
  } finally {
    loading.value = false;
    await nextTick();
    if (!error.value) {
      renderPlatformChart();
      renderSirChart();
      renderMicChart();
      await renderGermanyMap();
    }
  }
}

onMounted(() => {
  window.addEventListener("resize", handleResize);
  fetchGlobalStatistics();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [platformChartRef.value, sirChartRef.value, micChartRef.value].forEach((chartEl) => {
    if (chartEl && Plotly?.purge) {
      Plotly.purge(chartEl);
    }
  });
  if (germanyMap) {
    germanyMap.remove();
    germanyMap = null;
    germanyMarkersLayer = null;
    germanyStatesLayer = null;
  }
});
</script>

<style scoped>
.card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-wrap {
  min-height: 360px;
}

.plotly-chart {
  width: 100%;
  height: 340px;
}

.leaflet-map {
  width: 100%;
  height: 420px;
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
  background: #ffffff;
}

/* No tile layer, so the container's default grey would show through. */
:deep(.leaflet-container) {
  background: #ffffff;
}

:deep(.leaflet-interactive) {
  cursor: pointer;
  transition: fill 0.12s ease-in-out;
}

:deep(.germany-pin-marker) {
  background: transparent;
  border: none;
}

:deep(.germany-pin-marker .pin-drop) {
  position: relative;
  display: inline-block;
  background: #dc3545;
  border: 2px solid #ffffff;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  transition: background 0.12s ease-in-out;
}

:deep(.germany-pin-marker:hover .pin-drop) {
  background: #6c757d;
}

:deep(.leaflet-tooltip) {
  padding: 0.35rem 0.6rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  font-size: 0.8125rem;
  color: #212529;
}

/* Permanent Bundesland name labels - plain text, no bubble, sits under the pins. */
:deep(.leaflet-tooltip.state-name-label) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #97a1ab;
}

:deep(.leaflet-tooltip.state-name-label--small) {
  font-size: 0.55rem;
}

:deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  border-radius: 0.5rem;
  overflow: hidden;
}

:deep(.leaflet-control-zoom a) {
  width: 34px;
  height: 34px;
  line-height: 34px;
  background: #343a40;
  color: #ffffff;
  border: none;
  font-size: 1.1rem;
}

:deep(.leaflet-control-zoom a:hover) {
  background: #23272b;
  color: #ffffff;
}

:deep(.leaflet-control-zoom a.leaflet-disabled) {
  background: #6c757d;
  color: #dee2e6;
}

:deep(.germany-pin-marker .pin-drop::after) {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  width: 35%;
  height: 35%;
  background: #ffffff;
  border-radius: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
}
</style>
