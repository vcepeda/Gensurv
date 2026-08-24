<template>
  <div class="container mt-5 mb-5">
    <!-- Page Header -->
    <div class="mb-5 text-center">
      <h1>{{ contentLang.lang === 'de' ? 'Über uns' : 'About Us' }}</h1>
      <p class="lead">
        {{ contentLang.lang === 'de'
          ? 'Erfahren Sie mehr über unser Team, GenSurv und NUM-SAR.'
          : 'Learn more about our team, GenSurv, and NUM-SAR.' }}
      </p>
    </div>

    <!-- Our Team Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        {{ contentLang.lang === 'de' ? 'Unser Team' : 'Our Team' }}
      </div>
      <div class="card-body">
        <p>
          {{ contentLang.lang === 'de'
            ? 'Der GenSurv Data Hub ist Teil der Forschungsinfrastruktur NUM-SAR des Netzwerks Universitätsmedizin (NUM). Ziel von NUM-SAR ist es, Informationen bereitzustellen sowie eine Infrastruktur für die Universitätsmedizin zur Verfügung zu stellen, die weiterführende Forschung zu Aspekten des Pandemiemanagements ermöglicht.'
            : 'The GenSurv Data Hub is part of the NUM-SAR research infrastructure of the Network of University Medicine (NUM). The goal of NUM-SAR is to provide information and an infrastructure for university medical centers that enables further research into aspects of pandemic management.' }}
        </p>
        <template v-if="contentLang.lang === 'de'">
          <div v-for="group in teamDe" :key="group.institution" class="team-group mb-4">
            <h6 class="team-institution">{{ group.institution }}</h6>
            <ul class="list-unstyled team-list mb-0">
              <li v-for="person in group.people" :key="person.name" class="mb-3">
                <strong>{{ person.name }}</strong><br>
                <span class="text-muted">{{ person.role }}</span>
              </li>
            </ul>
          </div>
        </template>
        <template v-else>
          <div v-for="group in teamEn" :key="group.institution" class="team-group mb-4">
            <h6 class="team-institution">{{ group.institution }}</h6>
            <ul class="list-unstyled team-list mb-0">
              <li v-for="person in group.people" :key="person.name" class="mb-3">
                <strong>{{ person.name }}</strong><br>
                <span class="text-muted">{{ person.role }}</span>
              </li>
            </ul>
          </div>
        </template>
      </div>
    </div>

    <!-- About GenSurv Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        {{ contentLang.lang === 'de' ? 'Über GenSurv' : 'About GenSurv' }}
      </div>
      <div class="card-body">
        <template v-if="contentLang.lang === 'de'">
          <p>
            Gemeinsam mit dem Robert Koch-Institut (RKI) und weiteren Expertinnen und Experten
            entwickelt GenSurv ein nationales Netzwerk für die genomische Erreger-Surveillance,
            indem es für die Surveillance relevante Strategien, Technologien und Expertisen
            effizient zusammenführt, bewertet, (weiter-)entwickelt und zur gemeinsamen Nutzung zur
            Verfügung stellt. Dazu gehören insbesondere Strategien zur Auswahl und Beprobung
            relevanter Infektionserreger, der Aufbau einer Dateninfrastruktur zur Speicherung und
            Analyse von Infektionserreger-Sequenzierungsdaten sowie eine Verknüpfung dieser Daten
            mit ausgewählten Informationen zum Verhalten des Erregers und dem Kontext, in dem die
            Infektion erfolgte. GenSurv ist grundsätzlich skalierbar und international
            anschlussfähig konzipiert. Das Modul basiert auf vertrauensvoller institutions-,
            sektoren- und professionsübergreifender und überregionaler Zusammenarbeit. Die
            Prinzipien der Offenheit, Kollaboration, Qualitätssicherung und Effizienz gemäß der
            FAIR-Prinzipien stellen die Basis der Zusammenarbeit dar.
          </p>
          <p>
            Diese Plattform dient als gemeinsames bioinformatisches Ressourcenzentrum für Projekte
            der genomischen Erregersurveillance im Rahmen des Netzwerks Universitätsmedizin (NUM)
            und beherbergt derzeit <strong>GenSurv</strong> (<strong>NUM-SAR</strong>),
            <strong>GenSurv+</strong> und <strong>COGDAT</strong>.
          </p>
          <p class="mb-0">
            Unser Ziel ist es, teilnehmenden Kliniken und Laboren eine zentrale Anlaufstelle zu
            bieten, um Sequenzierdaten einzureichen, den Status ihrer Analysen zu verfolgen und
            auf die daraus resultierenden genomischen und epidemiologischen Erkenntnisse
            zuzugreifen — und so die frühzeitige Erkennung neu auftretender Erreger und Ausbrüche
            in Deutschland zu unterstützen.
          </p>
        </template>
        <template v-else>
          <p>
            Together with the Robert Koch-Institute (RKI) and other experts, GenSurv is developing
            a national network for genomic pathogen surveillance by efficiently bringing together,
            evaluating and (further) developing strategies, technologies and expertise relevant to
            surveillance and making them available for joint use. In particular, this includes
            strategies for the selection and sampling of relevant infectious agents, the
            establishment of a data infrastructure for the storage and analysis of infectious
            agent sequencing data and the linking of this data with selected information on the
            behaviour of the pathogen and the context in which the infection occurred. GenSurv is
            designed to be scalable and internationally compatible. The module is based on
            trusting cross-institutional, cross-sector and cross-professional and supra-regional
            collaboration. The principles of openness, collaboration, quality assurance and
            efficiency in accordance with the FAIR principles form the basis of the collaboration.
          </p>
          <p>
            The GenSurv Data Hub serves therefore as a shared bioinformatics resource center for
            genomic pathogen surveillance projects run under the Network of University Medicine
            (NUM), currently hosting <strong>GenSurv</strong> (<strong>NUM-SAR</strong>),
            <strong>GenSurv+</strong> and <strong>COGDAT</strong>.
          </p>
          <p class="mb-0">
            Our goal is to give participating hospitals and laboratories a single place to submit
            sequencing data, track the status of their analyses, and access the resulting genomic
            and epidemiological insights — supporting earlier detection of emerging pathogens and
            outbreaks across Germany.
          </p>
        </template>
      </div>
    </div>

    <!-- About NUM-SAR Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        {{ contentLang.lang === 'de' ? 'Über NUM-SAR' : 'About NUM-SAR' }}
      </div>
      <div class="card-body">
        <template v-if="contentLang.lang === 'de'">
          <p>
            Der GenSurv Data Hub ist Teil der Forschungsinfrastruktur NUM-SAR des Netzwerks
            Universitätsmedizin (NUM). Ziel von NUM-SAR ist es, Informationen bereitzustellen
            sowie eine Infrastruktur für die Universitätsmedizin zur Verfügung zu stellen, die
            weiterführende Forschung zu Aspekten des Pandemiemanagements ermöglicht.
          </p>
          <p class="mb-0">
            Die Leitung setzt sich zusammen aus Prof. Dr. Christian Drosten, Prof. Dr. Nicole
            Skoetz, Prof. Dr. Simone Scheithauer und Prof. Dr. Sven Zenker.
          </p>
        </template>
        <template v-else>
          <p>
            The GenSurv Data Hub is part of the NUM-SAR research infrastructure of the Network of
            University Medicine (NUM). The goal of NUM-SAR is to provide information and an
            infrastructure for university medical centers that enables further research into
            aspects of pandemic management.
          </p>
          <p class="mb-0">
            The project leads are Prof. Dr. Christian Drosten, Prof. Dr. Nicole Skoetz, Prof. Dr.
            Simone Scheithauer and Prof. Dr. Sven Zenker.
          </p>
        </template>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useContentLanguageStore } from "@/stores/contentLanguage";

const contentLang = useContentLanguageStore();

// Institution names and department names are kept in German in both language
// versions - same convention as the institution list below, and official
// department names don't have a settled English translation.
const teamDe = [
  {
    institution: "Charité – Universitätsmedizin Berlin",
    people: [
      { name: "Prof. Dr. Christian Drosten", role: "NUM-SAR Sprecher; Institut für Virologie" },
    ],
  },
  {
    institution: "Universitätsklinikum OWL der Universität Bielefeld",
    people: [
      { name: "Airin Franke", role: "GenSurv Koordination / Wissenschaftlerin; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
      { name: "Univ.-Prof. Dr. Claudia Hornberg", role: "GenSurv Sprecherin; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
      { name: "Prof. Dr. Alexander Sczyrba", role: "GenSurv Task-Lead; Centrum für Biotechnologie – CeBiTec" },
      { name: "Markus Tröger", role: "GenSurv Koordination / Wissenschaftler; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
    ],
  },
  {
    institution: "Universitätsklinikum der Ruhr-Universität Bochum",
    people: [
      { name: "Prof. Dr. Sören Gatermann", role: "GenSurv Task-Lead; Abteilung für Medizinische Mikrobiologie, Institut für Hygiene und Infektiologie" },
    ],
  },
  {
    institution: "Universitätsklinikum Düsseldorf",
    people: [
      { name: "Univ.-Prof. Dr. Alexander Dilthey", role: "GenSurv Sprecher; Medizinische Mikrobiologie und Krankenhaushygiene" },
    ],
  },
  {
    institution: "Universitätsklinikum Freiburg",
    people: [
      { name: "Dr. Jonas Fuchs", role: "GenSurv Wissenschaftler; Institut für Virologie" },
      { name: "Dr. Udo Gieraths", role: "GenSurv Wissenschaftler; Institut für Virologie" },
      { name: "Dr. Sandra Reuter", role: "GenSurv Task-Lead; Institut für Infektionsprävention und Krankenhaushygiene" },
      { name: "Prof. Dr. Marcus Panning", role: "GenSurv Task-Lead; Institut für Virologie" },
    ],
  },
  {
    institution: "Universitätsmedizin Göttingen",
    people: [
      { name: "Anna Bludau", role: "GenSurv Koordination / Wissenschaftlerin; Institut für Hygiene und Infektiologie" },
      { name: "PD Dr. Ulrike Loderstädt", role: "GenSurv Sprecherin (stellv.); Institut für Hygiene und Infektiologie" },
      { name: "Univ.-Prof. Dr. Simone Scheithauer", role: "NUM-SAR Co-Sprecherin, MuSE Sprecherin; Institut für Hygiene und Infektiologie" },
    ],
  },
  {
    institution: "Universitätsklinikum Tübingen",
    people: [
      { name: "Dr. Victoria Paz Cepeda Espinoza", role: "GenSurv Wissenschaftlerin; Institut für Medizinische Genetik und Angewandte Genomik; Website-Entwicklung & Wartung" },
      { name: "Jana Lorenz", role: "Mitarbeiterin, Analyse von Plasmiden und mobilen genetischen Elementen; Universität Tübingen (Masterstudentin)" },
      { name: "Siddharth-Avdhesh Pandey", role: "Website-Entwicklung; Universität Tübingen" },
      { name: "Prof. Dr. Stephan Ossowski", role: "GenSurv Task Lead; Institut für Medizinische Genetik und Angewandte Genomik" },
    ],
  },
];

const teamEn = [
  {
    institution: "Charité – Universitätsmedizin Berlin",
    people: [
      { name: "Prof. Dr. Christian Drosten", role: "NUM-SAR Spokesperson; Institut für Virologie" },
    ],
  },
  {
    institution: "Universitätsklinikum OWL der Universität Bielefeld",
    people: [
      { name: "Airin Franke", role: "GenSurv Coordination / Researcher; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
      { name: "Univ.-Prof. Dr. Claudia Hornberg", role: "GenSurv Spokesperson; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
      { name: "Prof. Dr. Alexander Sczyrba", role: "GenSurv Task Lead; Centrum für Biotechnologie – CeBiTec" },
      { name: "Markus Tröger", role: "GenSurv Coordination / Researcher; Medizinische Fakultät OWL, AG Sustainable Environmental Health Sciences" },
    ],
  },
  {
    institution: "Universitätsklinikum der Ruhr-Universität Bochum",
    people: [
      { name: "Prof. Dr. Sören Gatermann", role: "GenSurv Task Lead; Abteilung für Medizinische Mikrobiologie, Institut für Hygiene und Infektiologie" },
    ],
  },
  {
    institution: "Universitätsklinikum Düsseldorf",
    people: [
      { name: "Univ.-Prof. Dr. Alexander Dilthey", role: "GenSurv Spokesperson; Medizinische Mikrobiologie und Krankenhaushygiene" },
    ],
  },
  {
    institution: "Universitätsklinikum Freiburg",
    people: [
      { name: "Dr. Jonas Fuchs", role: "GenSurv Researcher; Institut für Virologie" },
      { name: "Dr. Udo Gieraths", role: "GenSurv Researcher; Institut für Virologie" },
      { name: "Dr. Sandra Reuter", role: "GenSurv Task Lead; Institut für Infektionsprävention und Krankenhaushygiene" },
      { name: "Prof. Dr. Marcus Panning", role: "GenSurv Task Lead; Institut für Virologie" },
    ],
  },
  {
    institution: "Universitätsmedizin Göttingen",
    people: [
      { name: "Anna Bludau", role: "GenSurv Coordination / Researcher; Institut für Hygiene und Infektiologie" },
      { name: "PD Dr. Ulrike Loderstädt", role: "GenSurv Deputy Spokesperson; Institut für Hygiene und Infektiologie" },
      { name: "Univ.-Prof. Dr. Simone Scheithauer", role: "NUM-SAR Co-Spokesperson, MuSE Spokesperson; Institut für Hygiene und Infektiologie" },
    ],
  },
  {
    institution: "Universitätsklinikum Tübingen",
    people: [
      { name: "Dr. Victoria Paz Cepeda Espinoza", role: "GenSurv Researcher; Institut für Medizinische Genetik und Angewandte Genomik; Website development & maintenance" },
      { name: "Jana Lorenz", role: "Contributor, plasmid and mobile genetic element analysis; Universität Tübingen (Master's student)" },
      { name: "Siddharth Avdhesh Pandey", role: "Website development; University of Tübingen" },
      { name: "Prof. Dr. Stephan Ossowski", role: "GenSurv Task Lead; Institut für Medizinische Genetik und Angewandte Genomik" },
    ],
  },
];
</script>

<style scoped>
/* Optional: subtle background consistency with other static pages */
.container {
  max-width: 960px;
}

.team-institution {
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6c757d;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.team-group:last-child {
  margin-bottom: 0 !important;
}
</style>
