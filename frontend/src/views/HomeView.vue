<template>
  <div class="container-fluid py-3">
    <div class="text-center mb-4">
      <h1>Genomic Pathogen Surveillance Data Hub</h1>
      <p class="lead">{{ t.heroLead }}</p>
    </div>

    <!-- Platform at a Glance -->
    <div class="card mb-5 shadow-sm">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">{{ t.glanceTitle }}</h5>
      </div>
      <div class="card-body">
        <div v-if="statsLoading" class="text-center py-3">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ t.loading }}</span>
          </div>
        </div>
        <div v-else-if="statsError" class="text-muted text-center py-2">
          {{ t.statsError }}
        </div>
        <div v-else class="row g-3">
          <div class="col-6 col-md-3">
            <div class="text-center p-3 border rounded">
              <h4 class="text-dark">{{ stats.total_submissions || 0 }}</h4>
              <p class="mb-0">{{ t.statSubmissions }}</p>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="text-center p-3 border rounded">
              <h4 class="text-dark">{{ stats.total_unique_sample_identifiers || 0 }}</h4>
              <p class="mb-0">{{ t.statSamples }}</p>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="text-center p-3 border rounded">
              <h4 class="text-dark">{{ stats.total_unique_isolate_species || 0 }}</h4>
              <p class="mb-0">{{ t.statSpecies }}</p>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="text-center p-3 border rounded">
              <h4 class="text-dark">{{ stats.total_fastq_files || 0 }}</h4>
              <p class="mb-0">{{ t.statFiles }}</p>
            </div>
          </div>
        </div>
        <div class="text-center mt-3">
          <RouterLink to="/statistics" class="btn btn-outline-primary btn-sm">{{ t.viewFullStatistics }}</RouterLink>
          <RouterLink to="/dashboard" class="btn btn-outline-secondary btn-sm ms-2">{{ t.viewDashboard }}</RouterLink>
        </div>
      </div>
    </div>

    <!-- Projects -->
    <div class="mb-5">
      <h3 class="text-center mb-4">{{ t.ourProjects }}</h3>
      <p class="text-center text-muted">{{ t.projectsIntro }}</p>
      <div class="row g-4">
        <div v-for="project in projects" :key="project.name" class="col-md-4">
          <div class="card h-100 shadow-sm">
            <div class="card-body d-flex flex-column">
              <img v-if="project.logo" :src="project.logo" :alt="`${project.name} logo`" class="project-logo mb-2">
              <h5 class="card-title">{{ project.name }}</h5>
              <p class="card-text flex-grow-1">{{ project.description }}</p>
              <div class="d-flex gap-2 flex-wrap">
                <template v-if="project.external">
                  <a :href="project.href" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
                    {{ visitLabel(project.name) }}
                  </a>
                </template>
                <template v-else>
                  <RouterLink :to="project.uploadTo" class="btn btn-primary btn-sm">{{ t.uploadData }}</RouterLink>
                  <RouterLink :to="project.helpTo" class="btn btn-outline-secondary btn-sm">{{ t.learnMore }}</RouterLink>
                  <a
                    v-if="project.aboutHref"
                    :href="project.aboutHref"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="btn btn-outline-secondary btn-sm"
                  >
                    {{ t.about }} {{ project.name }}
                  </a>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Publications Section -->
    <div class="card mb-5" id="publications">
      <div class="card-header">{{ t.publications }}</div>
      <div class="card-body">
        <h6 class="mb-2">{{ activePublication.title }}</h6>
        <p class="mb-2">{{ activePublication.text }}</p>

        <RouterLink :to="activePublication.to">{{ t.readMore }}</RouterLink>

        <div class="d-flex justify-content-center mt-3">
          <div class="pagination-dots">
            <span
              v-for="(_, i) in publications"
              :key="`pub-${i}`"
              class="dot"
              :class="{ active: i === pubIndex }"
              role="button"
              tabindex="0"
              @click="pubIndex = i"
              @keydown.enter="pubIndex = i"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Pipelines Section -->
    <div class="card mb-5" id="pipelines">
      <div class="card-header">{{ t.pipelines }}</div>
      <div class="card-body small-text">
        <h6 class="mb-2">{{ activePipeline.title }}</h6>
        <p class="mb-2">{{ activePipeline.text }}</p>

        <a :href="activePipeline.href" target="_blank" rel="noopener noreferrer">
          {{ t.readMore }}
        </a>

        <div class="d-flex justify-content-center mt-3">
          <div class="pagination-dots">
            <span
              v-for="(_, i) in pipelines"
              :key="`pipe-${i}`"
              class="dot"
              :class="{ active: i === pipeIndex }"
              role="button"
              tabindex="0"
              @click="pipeIndex = i"
              @keydown.enter="pipeIndex = i"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Collaborators Section -->
    <div class="card mb-5" id="collaborators">
      <div class="card-header">{{ t.collaboratorWebsites }}</div>
      <div class="card-body small-text">
        <h6 class="mb-2">{{ activeWebsite.title }}</h6>
        <p class="mb-2">{{ activeWebsite.text }}</p>

        <a :href="activeWebsite.href" target="_blank" rel="noopener noreferrer">
          {{ t.readMore }}
        </a>

        <div class="d-flex justify-content-center mt-3">
          <div class="pagination-dots">
            <span
              v-for="(_, i) in websites"
              :key="`web-${i}`"
              class="dot"
              :class="{ active: i === webIndex }"
              role="button"
              tabindex="0"
              @click="webIndex = i"
              @keydown.enter="webIndex = i"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import apiClient from "../api/client";
import { useContentLanguageStore } from "@/stores/contentLanguage";

const contentLang = useContentLanguageStore();
const pubIndex = ref(0);
const pipeIndex = ref(0);
const webIndex = ref(0);

const stats = ref({});
const statsLoading = ref(false);
const statsError = ref("");

const projectsEn = [
  {
    name: "Carbapenem resistant Enterobacterales",
    description: "Genomic pathogen surveillance for bacterial AMR — sequencing, antibiotic resistance profiling, and outbreak detection across German university hospitals.",
    uploadTo: "/upload/gensurv",
    helpTo: "/help/gensurv",
  },
  {
    name: "Norovirus",
    description: "Sequencing-based viral surveillance, with reporting aligned to RKI/DEMIS metadata requirements.",
    uploadTo: "/upload/num-sar",
    helpTo: "/help/num-sar",
    aboutHref: "https://www.netzwerk-universitaetsmedizin.de/plattformen/num-sar",
  },
  {
    name: "SARS-CoV-2",
    description: "SARS-CoV-2 genomic surveillance and lineage tracking, hosted on its own dedicated platform.",
    external: true,
    href: "https://cogdat.de/",
  },
];

const projectsDe = [
  {
    name: "GenSurv (NUM-SAR)",
    description: "Genomische Erregerüberwachung für bakterielle Antibiotikaresistenzen (AMR) — Sequenzierung, Resistenzprofilierung und Ausbruchserkennung an deutschen Universitätskliniken.",
    uploadTo: "/upload/gensurv",
    helpTo: "/help/gensurv",
  },
  {
    name: "NUM-SAR",
    description: "Sequenzierungsbasierte Überwachung antimikrobieller Resistenzen, mit Meldungen gemäß den Metadatenanforderungen von RKI/DEMIS.",
    uploadTo: "/upload/num-sar",
    helpTo: "/help/num-sar",
    aboutHref: "https://www.netzwerk-universitaetsmedizin.de/plattformen/num-sar",
  },
  {
    name: "COGDAT",
    description: "Genomische Überwachung und Linien-Tracking von SARS-CoV-2, betrieben auf einer eigenen dedizierten Plattform.",
    external: true,
    href: "https://cogdat.de/",
  },
];

const projects = computed(() => (contentLang.lang === "de" ? projectsDe : projectsEn));

async function fetchStats() {
  statsLoading.value = true;
  statsError.value = "";
  try {
    const res = await apiClient.get("/api/statistics/global/");
    stats.value = res.data || {};
  } catch (e) {
    statsError.value = "Failed to load statistics.";
  } finally {
    statsLoading.value = false;
  }
}

onMounted(fetchStats);

// Publication citations are bibliographic references in their original
// English - not translated, only the card titles are.
const publicationsEn = [
  {
    title: "Publications",
    text:
      "Analysis of a long-term outbreak of XDR Pseudomonas aeruginosa: a molecular epidemiological study. Willmann, M. et al. 2021",
    to: { path: "/research"},
  },
  {
    title: "Related Publications",
    text:
      "The genomic epidemiology of invasive pneumococcal disease in the United Kingdom prior to the introduction of the 13-valent pneumococcal conjugate vaccine. Miralles, M. T. et al. (2021).",
    to: { path: "/research"},
  },
];

const publicationsDe = [
  {
    title: "Publikationen",
    text:
      "Analysis of a long-term outbreak of XDR Pseudomonas aeruginosa: a molecular epidemiological study. Willmann, M. et al. 2021",
    to: { path: "/research"},
  },
  {
    title: "Verwandte Publikationen",
    text:
      "The genomic epidemiology of invasive pneumococcal disease in the United Kingdom prior to the introduction of the 13-valent pneumococcal conjugate vaccine. Miralles, M. T. et al. (2021).",
    to: { path: "/research"},
  },
];

const publications = computed(() => (contentLang.lang === "de" ? publicationsDe : publicationsEn));

const pipelinesEn = [
  {
    title: "Bactopia",
    text: "Bactopia is a flexible bioinformatics pipeline for complete analysis of bacterial genomes.",
    href: "https://bactopia.github.io/latest/",
  },
  {
    title: "Viralrecon",
    text: "A bioinformatics pipeline for viral genome sequencing data.",
    href: "https://nf-co.re/viralrecon",
  },
  {
    title: "MAG",
    text: "A pipeline for metagenome-assembled genomes.",
    href: "https://nf-co.re/mag",
  },
  {
    title: "plasmIDent",
    text: "A tool for identifying plasmids from sequencing data.",
    href: "https://github.com/imgag/plasmIDent",
  },
  {
    title: "COVID-19",
    text: "A pipeline for analyzing COVID-19 sequencing data.",
    href: "https://github.com/imgag/COVID-19",
  },
  {
    title: "VIPR",
    text: "A viral pathogen identification and sequencing pipeline.",
    href: "https://nf-co.re/vipr",
  },
];

const pipelinesDe = [
  {
    title: "Bactopia",
    text: "Bactopia ist eine flexible Bioinformatik-Pipeline für die vollständige Analyse bakterieller Genome.",
    href: "https://bactopia.github.io/latest/",
  },
  {
    title: "Viralrecon",
    text: "Eine Bioinformatik-Pipeline für die Sequenzierungsdaten viraler Genome.",
    href: "https://nf-co.re/viralrecon",
  },
  {
    title: "MAG",
    text: "Eine Pipeline für metagenomassemblierte Genome.",
    href: "https://nf-co.re/mag",
  },
  {
    title: "plasmIDent",
    text: "Ein Werkzeug zur Identifizierung von Plasmiden aus Sequenzierungsdaten.",
    href: "https://github.com/imgag/plasmIDent",
  },
  {
    title: "COVID-19",
    text: "Eine Pipeline zur Analyse von COVID-19-Sequenzierungsdaten.",
    href: "https://github.com/imgag/COVID-19",
  },
  {
    title: "VIPR",
    text: "Eine Pipeline zur Identifizierung und Sequenzierung viraler Erreger.",
    href: "https://nf-co.re/vipr",
  },
];

const pipelines = computed(() => (contentLang.lang === "de" ? pipelinesDe : pipelinesEn));

const websitesEn = [
  {
    title: "NUM Genomische Surveillance",
    text: "A project focused on genomic surveillance of infectious diseases in Germany.",
    href: "https://num-genomische-surveillance.de/",
  },
  {
    title: "Netzwerk Universitätsmedizin",
    text: "Collaborative research to improve healthcare and patient outcomes.",
    href: "https://www.netzwerk-universitaetsmedizin.de/en/projects/gensurv",
  },
  {
    title: "UMG Forschung Corona",
    text: "Research initiatives on COVID-19 at UMG.",
    href: "https://www.umg.eu/en/forschung/corona/num/gensurv/",
  },
  {
    title: "Charité NUM Projekte",
    text: "Ongoing research projects at Charité related to NUM.",
    href: "https://num.charite.de/teilprojekte/laufende_projekte/gensurv/",
  },
  {
    title: "UMG Forschung Labore",
    text: "Laboratory research projects at UMG.",
    href: "https://hyg-infekt.umg.eu/forschung-labore/projekte/num3/",
  },
];

const websitesDe = [
  {
    title: "NUM Genomische Surveillance",
    text: "Ein Projekt mit Fokus auf die genomische Überwachung von Infektionskrankheiten in Deutschland.",
    href: "https://num-genomische-surveillance.de/",
  },
  {
    title: "Netzwerk Universitätsmedizin",
    text: "Gemeinsame Forschung zur Verbesserung der Gesundheitsversorgung und der Behandlungsergebnisse.",
    href: "https://www.netzwerk-universitaetsmedizin.de/en/projects/gensurv",
  },
  {
    title: "UMG Forschung Corona",
    text: "Forschungsinitiativen zu COVID-19 an der UMG.",
    href: "https://www.umg.eu/en/forschung/corona/num/gensurv/",
  },
  {
    title: "Charité NUM Projekte",
    text: "Laufende NUM-bezogene Forschungsprojekte an der Charité.",
    href: "https://num.charite.de/teilprojekte/laufende_projekte/gensurv/",
  },
  {
    title: "UMG Forschung Labore",
    text: "Laborforschungsprojekte an der UMG.",
    href: "https://hyg-infekt.umg.eu/forschung-labore/projekte/num3/",
  },
];

const websites = computed(() => (contentLang.lang === "de" ? websitesDe : websitesEn));

const activePublication = computed(() => publications.value[pubIndex.value]);
const activePipeline = computed(() => pipelines.value[pipeIndex.value]);
const activeWebsite = computed(() => websites.value[webIndex.value]);

const T_EN = {
  heroLead:
    "A genomic pathogen surveillance data hub for Germany, part of the NUM-SAR platform under the Network of University Medicine (NUM) — supporting data submission for GenSurv, NUM-SAR, and COGDAT.",
  glanceTitle: "Platform at a Glance",
  loading: "Loading...",
  statsError: "Live statistics are temporarily unavailable.",
  statSubmissions: "Submissions",
  statSamples: "Unique Samples",
  statSpecies: "Species Tracked",
  statFiles: "Sequencing Files",
  viewFullStatistics: "View Full Statistics",
  viewDashboard: "View Dashboard",
  ourProjects: "Our Projects",
  projectsIntro: "We are generally designed to support all bacteria and viruses, but we have defined use cases for testing the data hub.",
  visit: (name) => `Visit ${name}`,
  uploadData: "Upload Data",
  learnMore: "Learn More",
  about: "About",
  publications: "Publications",
  pipelines: "Bioinformatics Pipelines",
  collaboratorWebsites: "Collaborator Websites",
  readMore: "Read more",
};

const T_DE = {
  heroLead:
    "Ein Daten-Hub für die genomische Erregerüberwachung in Deutschland, Teil der NUM-SAR-Plattform des Netzwerks Universitätsmedizin (NUM) — zur Unterstützung der Datenübermittlung für GenSurv, NUM-SAR und COGDAT.",
  glanceTitle: "Die Plattform im Überblick",
  loading: "Wird geladen...",
  statsError: "Live-Statistiken sind vorübergehend nicht verfügbar.",
  statSubmissions: "Einreichungen",
  statSamples: "Eindeutige Proben",
  statSpecies: "Erfasste Spezies",
  statFiles: "Sequenzierungsdateien",
  viewFullStatistics: "Vollständige Statistiken ansehen",
  viewDashboard: "Dashboard ansehen",
  ourProjects: "Unsere Projekte",
  projectsIntro: "Wir sind grundsätzlich für alle Bakterien und Viren ausgelegt, haben jedoch definierte Anwendungsfälle zum Testen des Data Hubs festgelegt.",
  visit: (name) => `${name} besuchen`,
  uploadData: "Daten hochladen",
  learnMore: "Mehr erfahren",
  about: "Über",
  publications: "Publikationen",
  pipelines: "Bioinformatik-Pipelines",
  collaboratorWebsites: "Websites der Kooperationspartner",
  readMore: "Weiterlesen",
};

const t = computed(() => (contentLang.lang === "de" ? T_DE : T_EN));

function visitLabel(name) {
  return t.value.visit(name);
}
</script>

<style scoped>
.project-logo {
  max-height: 40px;
  width: auto;
  align-self: flex-start;
}

.small-text {
  font-size: 0.95rem;
}

.pagination-dots {
  display: flex;
  gap: 10px;
  align-items: center;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ddd;
  display: inline-block;
  cursor: pointer;
  user-select: none;
}

.dot.active {
  background: #717171;
}
</style>
