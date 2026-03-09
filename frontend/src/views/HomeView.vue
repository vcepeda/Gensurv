<template>
  <div class="container-fluid py-3">
    <div class="text-center mb-4">
      <h2>GENSURV BIOINFORMATICS RESOURCE CENTER</h2>
    </div>

    <!-- Overview Section -->
    <div class="mb-5">
      <h3 id="overview">Gensurv Overview</h3>
      <p>
        The Genomic pathogen surveillance in German initiative, also known as "GenSurv," is a public
        health initiative aimed at monitoring and tracking the spread of infectious diseases in
        Germany using genomic sequencing technology. The goal of GenSurv is to detect and identify
        emerging pathogens and outbreaks early, which can help public health officials respond more
        quickly to contain and control the spread of disease.
      </p>
      <p>
        GenSurv involves sequencing the genomes of infectious agents, such as viruses and bacteria,
        found in patient samples collected from hospitals, clinics, and other healthcare facilities
        across Germany. The genomic data is then analyzed to identify patterns of transmission and
        genetic changes in the pathogens over time. This information can help researchers and
        public health officials understand how the disease is spreading, identify potential sources
        of infection, and develop strategies to prevent and control outbreaks.
      </p>
      <p>
        Overall, the goal of GenSurv is to improve public health preparedness and response to
        infectious disease outbreaks in Germany by using genomic sequencing technology to track and
        monitor the spread of pathogens in real-time.
      </p>
      <p>
        GenSurv is a collaborative effort between several institutions and organizations in Germany,
        including the Robert Koch Institute (RKI), the National Reference Center for Tropical
        Pathogens at the Bernhard Nocht Institute for Tropical Medicine (BNITM), and several
        university and hospital partners.
      </p>
    </div>

    <!-- NUM Section -->
    <div class="mb-5">
      <h3 id="num">GenSurv and the Network of University Medicine (NUM)</h3>
      <p>
        GenSurv is part of the Network of University Medicine (NUM).
      </p>
      <p>
        Within the NUM, all 36 German university hospitals are, for the first time, jointly carrying
        out large-scale interdisciplinary research projects. The network was launched in 2020 to
        coordinate COVID-19 research across all university hospitals. In the future, the NUM will
        research further diseases and involve as many partners as possible from medical science,
        health care, and society.
      </p>
      <p>
        The NUM focuses in particular on clinical research, the results of which directly support
        patient care. One major area of NUM activity is the joint collection and use of complex
        medical research data. To this end, the network has set up research infrastructures with
        which it is helping to better prepare the German healthcare system for future pandemics and
        crises.
      </p>
      <p>
        The NUM is funded by the German Federal Ministries of Education and Research and is
        coordinated by "Charité – Universitätsmedizin Berlin."
      </p>
      <p class="mb-0">
        More information can be found at:
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
      <div class="card-header">Publications</div>
      <div class="card-body">
        <h6 class="mb-2">{{ activePublication.title }}</h6>
        <p class="mb-2">{{ activePublication.text }}</p>

        <RouterLink :to="activePublication.to">Read more</RouterLink>

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
      <div class="card-header">Bioinformatics Pipelines</div>
      <div class="card-body small-text">
        <h6 class="mb-2">{{ activePipeline.title }}</h6>
        <p class="mb-2">{{ activePipeline.text }}</p>

        <a :href="activePipeline.href" target="_blank" rel="noopener noreferrer">
          Read more
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
      <div class="card-header">Collaborator Websites</div>
      <div class="card-body small-text">
        <h6 class="mb-2">{{ activeWebsite.title }}</h6>
        <p class="mb-2">{{ activeWebsite.text }}</p>

        <a :href="activeWebsite.href" target="_blank" rel="noopener noreferrer">
          Read more
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
import { ref, computed } from "vue";

const pubIndex = ref(0);
const pipeIndex = ref(0);
const webIndex = ref(0);

const publications = [
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

const pipelines = [
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

const websites = [
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

const activePublication = computed(() => publications[pubIndex.value]);
const activePipeline = computed(() => pipelines[pipeIndex.value]);
const activeWebsite = computed(() => websites[webIndex.value]);
</script>

<style scoped>
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
