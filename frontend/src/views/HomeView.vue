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

    <!-- Overview Section -->
    <div class="mb-5">
      <h3 id="overview">{{ t.gensurvOverviewTitle }}</h3>
      <p v-for="(para, i) in t.gensurvOverviewParagraphs" :key="`gensurv-p-${i}`">{{ para }}</p>
    </div>

    <!-- NUM-SAR Overview Section -->
    <div class="mb-5">
      <h3 id="num-sar-overview">{{ t.numSarOverviewTitle }}</h3>
      <p>{{ t.numSarOverviewParagraph1 }}</p>
      <p class="mb-0">
        {{ t.numSarOverviewParagraph2 }}
        <a
          href="https://www.netzwerk-universitaetsmedizin.de/plattformen/num-sar"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://www.netzwerk-universitaetsmedizin.de/plattformen/num-sar
        </a>.
      </p>
    </div>

    <!-- COGDAT Overview Section -->
    <div class="mb-5">
      <h3 id="cogdat-overview">{{ t.cogdatOverviewTitle }}</h3>
      <p class="mb-0">
        {{ t.cogdatOverviewParagraph }}
        <a href="https://cogdat.de/" target="_blank" rel="noopener noreferrer">cogdat.de</a>.
      </p>
    </div>

    <!-- NUM Section -->
    <div class="mb-5">
      <h3 id="num">{{ t.numSectionTitle }}</h3>
      <p v-for="(para, i) in t.numSectionParagraphs" :key="`num-p-${i}`">{{ para }}</p>
      <p class="mb-0">
        {{ t.moreInfoAt }}
        <a
          href="https://www.netzwerk-universitaetsmedizin.de"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://www.netzwerk-universitaetsmedizin.de
        </a>.
      </p>
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
import gensurvLogo from "../assets/gensurv-removebg-preview.png";
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
    name: "GenSurv",
    logo: gensurvLogo,
    description: "Genomic pathogen surveillance for bacterial AMR — sequencing, antibiotic resistance profiling, and outbreak detection across German university hospitals.",
    uploadTo: "/upload/gensurv",
    helpTo: "/help/gensurv",
  },
  {
    name: "NUM-SAR",
    description: "Sequencing-based antimicrobial resistance surveillance, with reporting aligned to RKI/DEMIS metadata requirements.",
    uploadTo: "/upload/num-sar",
    helpTo: "/help/num-sar",
    aboutHref: "https://www.netzwerk-universitaetsmedizin.de/plattformen/num-sar",
  },
  {
    name: "COGDAT",
    description: "SARS-CoV-2 genomic surveillance and lineage tracking, hosted on its own dedicated platform.",
    external: true,
    href: "https://cogdat.de/",
  },
];

const projectsDe = [
  {
    name: "GenSurv",
    logo: gensurvLogo,
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
  visit: (name) => `Visit ${name}`,
  uploadData: "Upload Data",
  learnMore: "Learn More",
  about: "About",
  gensurvOverviewTitle: "Gensurv Overview",
  gensurvOverviewParagraphs: [
    "The Genomic pathogen surveillance in German initiative, also known as \"GenSurv,\" is a public health initiative aimed at monitoring and tracking the spread of infectious diseases in Germany using genomic sequencing technology. The goal of GenSurv is to detect and identify emerging pathogens and outbreaks early, which can help public health officials respond more quickly to contain and control the spread of disease.",
    "GenSurv involves sequencing the genomes of infectious agents, such as viruses and bacteria, found in patient samples collected from hospitals, clinics, and other healthcare facilities across Germany. The genomic data is then analyzed to identify patterns of transmission and genetic changes in the pathogens over time. This information can help researchers and public health officials understand how the disease is spreading, identify potential sources of infection, and develop strategies to prevent and control outbreaks.",
    "Overall, the goal of GenSurv is to improve public health preparedness and response to infectious disease outbreaks in Germany by using genomic sequencing technology to track and monitor the spread of pathogens in real-time.",
    "GenSurv is a collaborative effort between several institutions and organizations in Germany, including the Robert Koch Institute (RKI), the National Reference Center for Tropical Pathogens at the Bernhard Nocht Institute for Tropical Medicine (BNITM), and several university and hospital partners.",
  ],
  numSarOverviewTitle: "NUM-SAR Overview",
  numSarOverviewParagraph1:
    "NUM-SAR (\"NUM-Plattform für Surveillance und Rapid Response\") is the Network of University Medicine's platform for pandemic preparedness and rapid response. It coordinates several specialized modules across German university hospitals — including pathogen diagnostics (PAKOP), evidence synthesis (ESVE), health-system monitoring (MuSE), a real-time dashboard, and GenSurv's genomic surveillance data hub — to detect pathogens early and support real-time decision-making.",
  numSarOverviewParagraph2:
    "This site handles NUM-SAR's sequencing-based antimicrobial resistance (AMR) surveillance data submission, with reporting aligned to RKI/DEMIS metadata requirements. More information on the full NUM-SAR platform can be found at:",
  cogdatOverviewTitle: "COGDAT Overview",
  cogdatOverviewParagraph:
    "COGDAT supports SARS-CoV-2 genomic surveillance in Germany, covering consensus sequence lineage assignment (Pangolin) and reporting of sequencing data to public health and international repositories such as RKI and GISAID. COGDAT is run on its own dedicated platform at",
  numSectionTitle: "The Network of University Medicine (NUM)",
  numSectionParagraphs: [
    "Within the NUM, all 36 German university hospitals are, for the first time, jointly carrying out large-scale interdisciplinary research projects. The network was launched in 2020 to coordinate COVID-19 research across all university hospitals. In the future, the NUM will research further diseases and involve as many partners as possible from medical science, health care, and society.",
    "The NUM focuses in particular on clinical research, the results of which directly support patient care. One major area of NUM activity is the joint collection and use of complex medical research data. To this end, the network has set up research infrastructures with which it is helping to better prepare the German healthcare system for future pandemics and crises.",
    "The NUM is funded by the German Federal Ministries of Education and Research and is coordinated by \"Charité – Universitätsmedizin Berlin.\"",
  ],
  moreInfoAt: "More information can be found at:",
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
  visit: (name) => `${name} besuchen`,
  uploadData: "Daten hochladen",
  learnMore: "Mehr erfahren",
  about: "Über",
  gensurvOverviewTitle: "GenSurv im Überblick",
  gensurvOverviewParagraphs: [
    "Die Initiative \"Genomische Erregerüberwachung in Deutschland\", bekannt als \"GenSurv\", ist eine Public-Health-Initiative, die mithilfe genomischer Sequenzierungstechnologien die Ausbreitung von Infektionskrankheiten in Deutschland überwacht und verfolgt. Ziel von GenSurv ist es, neu auftretende Erreger und Ausbrüche frühzeitig zu erkennen und zu identifizieren, damit Gesundheitsbehörden schneller reagieren können, um die Ausbreitung von Krankheiten einzudämmen und zu kontrollieren.",
    "Im Rahmen von GenSurv werden die Genome von Erregern wie Viren und Bakterien sequenziert, die in Patientenproben aus Krankenhäusern, Kliniken und anderen Gesundheitseinrichtungen in ganz Deutschland gesammelt wurden. Die genomischen Daten werden anschließend analysiert, um Übertragungsmuster und genetische Veränderungen der Erreger im Zeitverlauf zu erkennen. Diese Informationen helfen Forschenden und Gesundheitsbehörden zu verstehen, wie sich eine Krankheit ausbreitet, mögliche Infektionsquellen zu identifizieren und Strategien zur Prävention und Eindämmung von Ausbrüchen zu entwickeln.",
    "Insgesamt verfolgt GenSurv das Ziel, die Vorbereitung und Reaktionsfähigkeit des öffentlichen Gesundheitswesens in Deutschland auf Ausbrüche von Infektionskrankheiten zu verbessern, indem genomische Sequenzierungstechnologie zur Echtzeitverfolgung und -überwachung der Erregerausbreitung eingesetzt wird.",
    "GenSurv ist ein Gemeinschaftsprojekt mehrerer Institutionen und Organisationen in Deutschland, darunter das Robert Koch-Institut (RKI), das Nationale Referenzzentrum für tropische Infektionserreger am Bernhard-Nocht-Institut für Tropenmedizin (BNITM) sowie mehrere universitäre und klinische Partner.",
  ],
  numSarOverviewTitle: "NUM-SAR im Überblick",
  numSarOverviewParagraph1:
    "NUM-SAR (\"NUM-Plattform für Surveillance und Rapid Response\") ist die Plattform des Netzwerks Universitätsmedizin für Pandemievorsorge und schnelle Reaktionsfähigkeit. Sie koordiniert mehrere spezialisierte Module an deutschen Universitätskliniken — darunter Erregerdiagnostik (PAKOP), Evidenzsynthese (ESVE), Gesundheitssystem-Monitoring (MuSE), ein Echtzeit-Dashboard sowie den genomischen Surveillance-Datenhub von GenSurv —, um Erreger frühzeitig zu erkennen und Entscheidungen in Echtzeit zu unterstützen.",
  numSarOverviewParagraph2:
    "Diese Website übernimmt die sequenzierungsbasierte Datenübermittlung zur Überwachung antimikrobieller Resistenzen (AMR) im Rahmen von NUM-SAR, mit Meldungen gemäß den Metadatenanforderungen von RKI/DEMIS. Weitere Informationen zur gesamten NUM-SAR-Plattform finden Sie unter:",
  cogdatOverviewTitle: "COGDAT im Überblick",
  cogdatOverviewParagraph:
    "COGDAT unterstützt die genomische Überwachung von SARS-CoV-2 in Deutschland, einschließlich der Zuordnung von Konsensussequenzen zu Viruslinien (Pangolin) und der Meldung von Sequenzierungsdaten an Gesundheitsbehörden und internationale Datenbanken wie RKI und GISAID. COGDAT wird auf einer eigenen dedizierten Plattform betrieben unter",
  numSectionTitle: "Das Netzwerk Universitätsmedizin (NUM)",
  numSectionParagraphs: [
    "Im Rahmen des NUM führen erstmals alle 36 deutschen Universitätskliniken gemeinsam groß angelegte interdisziplinäre Forschungsprojekte durch. Das Netzwerk wurde 2020 gegründet, um die COVID-19-Forschung an allen Universitätskliniken zu koordinieren. Künftig wird das NUM weitere Erkrankungen erforschen und dabei möglichst viele Partner aus Medizin, Gesundheitsversorgung und Gesellschaft einbeziehen.",
    "Das NUM konzentriert sich insbesondere auf die klinische Forschung, deren Ergebnisse unmittelbar der Patientenversorgung zugutekommen. Ein wesentlicher Schwerpunkt der NUM-Aktivitäten ist die gemeinsame Erhebung und Nutzung komplexer medizinischer Forschungsdaten. Zu diesem Zweck hat das Netzwerk Forschungsinfrastrukturen aufgebaut, mit denen es dazu beiträgt, das deutsche Gesundheitssystem besser auf künftige Pandemien und Krisen vorzubereiten.",
    "Das NUM wird vom Bundesministerium für Bildung und Forschung gefördert und von der \"Charité – Universitätsmedizin Berlin\" koordiniert.",
  ],
  moreInfoAt: "Weitere Informationen finden Sie unter:",
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
