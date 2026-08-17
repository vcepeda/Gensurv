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

// Common German state abbreviations seen in submission metadata (e.g. "NRW"),
// resolved to the full-name keys used in germanStateCentroids above.
const germanStateAbbreviations = {
  bw: "badenwuerttemberg",
  by: "bayern",
  be: "berlin",
  bb: "brandenburg",
  hb: "bremen",
  hh: "hamburg",
  he: "hessen",
  mv: "mecklenburgvorpommern",
  ni: "niedersachsen",
  nw: "nordrheinwestfalen",
  nrw: "nordrheinwestfalen",
  rp: "rheinlandpfalz",
  sl: "saarland",
  sn: "sachsen",
  st: "sachsenanhalt",
  sh: "schleswigholstein",
  th: "thueringen",
};

// DEMIS/RKI reports anonymize patient location down to a 3-digit postal code
// prefix (no city name) - see
// https://wiki.gematik.de/spaces/DSKB/pages/659360260. These are Germany's
// well-known first-digit postal code zones, used as a coarse fallback so
// that data plots in roughly the right region instead of being scattered
// across the whole country or dropped entirely.
const germanPlzZoneCentroids = {
  0: { lat: 51.05, lon: 13.2 }, // Sachsen / Thueringen (Leipzig/Dresden area)
  1: { lat: 52.5, lon: 13.4 }, // Berlin / Brandenburg
  2: { lat: 53.55, lon: 10.0 }, // Hamburg / Schleswig-Holstein / Bremen
  3: { lat: 52.4, lon: 9.7 }, // Niedersachsen / Sachsen-Anhalt (Hannover area)
  4: { lat: 51.4, lon: 6.9 }, // NRW west (Ruhrgebiet/Duesseldorf)
  5: { lat: 50.8, lon: 7.0 }, // NRW south / Rheinland (Koeln/Bonn)
  6: { lat: 50.1, lon: 8.7 }, // Hessen / Rheinland-Pfalz south (Frankfurt)
  7: { lat: 48.8, lon: 9.2 }, // Baden-Wuerttemberg (Stuttgart)
  8: { lat: 48.3, lon: 11.6 }, // Bayern south (Muenchen)
  9: { lat: 49.6, lon: 11.0 }, // Bayern north / Sachsen east (Nuernberg)
};

// Human-readable name for each zone, used in the map popup so an anonymized
// postal code shows an actual region instead of just echoing the digits back.
const germanPlzZoneNames = {
  0: "Sachsen / Thueringen",
  1: "Berlin / Brandenburg",
  2: "Hamburg / Schleswig-Holstein / Bremen",
  3: "Niedersachsen / Sachsen-Anhalt",
  4: "Nordrhein-Westfalen (west)",
  5: "Nordrhein-Westfalen (south) / Rheinland",
  6: "Hessen / Rheinland-Pfalz / Saarland",
  7: "Baden-Wuerttemberg",
  8: "Bayern (south)",
  9: "Bayern (north) / Sachsen (east)",
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
  if (!key) return null;
  const resolvedKey = germanStateAbbreviations[key] || key;
  return germanStateCentroids[resolvedKey] || null;
}

function isPlausiblePostalCode(value) {
  return /^\d{2,5}$/.test(String(value || "").trim());
}

function extractPlzZoneDigit(value) {
  const text = String(value || "").trim();
  return isPlausiblePostalCode(text) ? text.charAt(0) : null;
}

function fallbackPointFromPlz(row) {
  const digit = extractPlzZoneDigit(row?.postal_code);
  return digit ? germanPlzZoneCentroids[digit] || null : null;
}

function plzRegionLabel(postalCode) {
  const digit = extractPlzZoneDigit(postalCode);
  const zoneName = digit ? germanPlzZoneNames[digit] : null;
  return zoneName
    ? `${zoneName} (approx., from anonymized postal code "${postalCode}")`
    : `Postal code "${postalCode}" (anonymized)`;
}

function resolveBaseLocation(row) {
  const stateBase = fallbackPointFromState(row);
  if (stateBase) return { point: stateBase, precision: "state" };
  const plzBase = fallbackPointFromPlz(row);
  if (plzBase) return { point: plzBase, precision: "plz-zone" };
  return { point: { lat: 51.1657, lon: 10.4515 }, precision: "unknown" };
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

const plzZoneRadius = { lat: 0.32, lon: 0.45 };
const stateRadius = { lat: 0.18, lon: 0.28 };
const unknownRadius = { lat: 0.55, lon: 0.75 };

function estimatePointFromRow(row) {
  const { point: base, precision } = resolveBaseLocation(row);
  const key = buildGermanyLocationKey(row);
  const hashA = hashString(key);
  const hashB = hashString(`${key}#b`);

  const factor = 0.35 + (hashA % 100) / 160;

  const radius = precision === "state" ? stateRadius : precision === "plz-zone" ? plzZoneRadius : unknownRadius;
  const latRadius = radius.lat;
  const lonRadius = radius.lon;
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
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(germanyMap);

  germanyMarkersLayer = L.layerGroup().addTo(germanyMap);
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

    const marker = L.marker([point.lat, point.lon], { icon: markerIcon(row.count) });
    const locationLabel = row.city
      ? [row.city, row.state].filter(Boolean).join(", ")
      : row.postal_code
      ? plzRegionLabel(row.postal_code)
      : row.state || "Germany";
    marker.bindPopup(`<strong>${locationLabel}</strong><br/>Count: ${row.count}`);
    marker.addTo(germanyMarkersLayer);
    bounds.push([point.lat, point.lon]);
  }

  if (bounds.length > 0) {
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

        const rawCity = normalizeLocationPart(row?.city);
        const rawState = normalizeLocationPart(row?.state);
        const rawPostal = normalizeLocationPart(row?.postal_code);

        // A city/state field containing a bare number is usually a DEMIS-style
        // anonymized 3-digit postal code entered into the wrong column, not a
        // real place name - don't display it as if it were one.
        const city = isPlausiblePostalCode(rawCity) ? "" : rawCity;
        const state = isPlausiblePostalCode(rawState) ? "" : rawState;
        const plzSource = [rawPostal, rawCity, rawState].find(isPlausiblePostalCode) || "";

        const hasState = Boolean(fallbackPointFromState({ state: rawState }));
        if (!city && !hasState && !plzSource) return; // nothing usable to place on the map

        // Group by city+state when a real city is known (regardless of postal
        // code, which can vary row-to-row for the same city - see Jena bug
        // below); fall back to postal-code+state grouping only when there's
        // no city, so distinct anonymized postal-code regions stay separate.
        const key = city
          ? `${city.toLowerCase()}|${(state || rawState).toLowerCase()}`
          : `${plzSource}|${(state || rawState).toLowerCase()}`;
        if (!cityAggregate.has(key)) {
          cityAggregate.set(key, {
            city,
            postal_code: plzSource,
            state: state || rawState,
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
  background: #f8f9fa;
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
