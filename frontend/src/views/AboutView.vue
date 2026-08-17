<template>
  <div class="container mt-5 mb-5">
    <!-- Page Header -->
    <div class="mb-5 text-center">
      <template v-if="contentLang.lang === 'de'">
        <h1>Über uns</h1>
        <p class="lead">
          Erfahren Sie mehr über unser Team und unser Leitbild.
        </p>
      </template>
      <template v-else>
        <h1>About Us</h1>
        <p class="lead">
          Learn more about our team and mission statement.
        </p>
      </template>
    </div>

    <!-- Our Team Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        {{ contentLang.lang === 'de' ? 'Unser Team' : 'Our Team' }}
      </div>
      <div class="card-body">
        <ul v-if="contentLang.lang === 'de'" class="list-unstyled team-list mb-0">
          <li class="mb-3">
            <strong>Victoria Cepeda-Espinoza</strong> — Postdoktorandin — Bioinformatik; Leitende Entwicklerin von GenSurv, einem Data Hub für die genomische Erregerüberwachung (bakterielle Genomik &amp; AMR-Pipelines)<br>
            <span class="text-muted">Universitätsklinikum Tübingen (UKT)</span>
          </li>
          <li class="mb-3">
            <strong>Siddharth-Avdhesh Pandey</strong> — Website-Entwicklung<br>
            <span class="text-muted">Universität Tübingen (Masterstudent, Maschinelles Lernen)</span>
          </li>
          <li class="mb-3">
            <strong>Jana Lorenz</strong> — Mitwirkende, Analyse von Plasmiden und mobilen genetischen Elementen<br>
            <span class="text-muted">Universität Tübingen (Masterstudentin, Bioinformatik)</span>
          </li>
          <li>
            <strong>Anna Bludau</strong> — Projektkoordinatorin<br>
            <span class="text-muted">Universitätsmedizin Göttingen</span>
          </li>
        </ul>
        <ul v-else class="list-unstyled team-list mb-0">
          <li class="mb-3">
            <strong>Victoria Cepeda-Espinoza</strong> — Postdoctoral Researcher — Bioinformatics; Lead developer of GenSurv, a genomic pathogen-surveillance data hub (bacterial genomics &amp; AMR pipelines)<br>
            <span class="text-muted">University Hospital Tübingen (UKT)</span>
          </li>
          <li class="mb-3">
            <strong>Siddharth-Avdhesh Pandey</strong> — Website development<br>
            <span class="text-muted">University of Tübingen (Master's student in ML)</span>
          </li>
          <li class="mb-3">
            <strong>Jana Lorenz</strong> — Contributor, plasmid and mobile genetic element analysis<br>
            <span class="text-muted">University of Tübingen (Master's student in Bioinformatics)</span>
          </li>
          <li>
            <strong>Anna Bludau</strong> — Project Coordinator<br>
            <span class="text-muted">Universitätsmedizin Göttingen</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Mission Statement Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        {{ contentLang.lang === 'de' ? 'Leitbild' : 'Mission Statement' }}
      </div>
      <div class="card-body">
        <template v-if="contentLang.lang === 'de'">
          <p>
            Diese Plattform dient als gemeinsames bioinformatisches Ressourcenzentrum für Projekte
            der genomischen Erregerüberwachung im Rahmen des Netzwerks Universitätsmedizin (NUM)
            und beherbergt derzeit <strong>GenSurv</strong>, <strong>NUM-SAR</strong> und
            <strong>COGDAT</strong>.
          </p>
          <p class="mb-0">
            Unser Ziel ist es, teilnehmenden Kliniken und Laboren eine zentrale Anlaufstelle zu
            bieten, um Sequenzierdaten einzureichen, den Status ihrer Analysen zu verfolgen und auf
            die daraus resultierenden genomischen und epidemiologischen Erkenntnisse zuzugreifen —
            und so die frühzeitige Erkennung neu auftretender Erreger und Ausbrüche in Deutschland
            zu unterstützen.
          </p>
        </template>
        <template v-else>
          <p>
            This platform serves as a shared bioinformatics resource center for genomic pathogen
            surveillance projects run under the Network of University Medicine (NUM), currently
            hosting <strong>GenSurv</strong>, <strong>NUM-SAR</strong>, and <strong>COGDAT</strong>.
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

    <!-- NUM-SAR / Participating Institutions Section -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header fw-semibold">
        NUM-SAR &amp; Participating Institutions
      </div>
      <div class="card-body">
        <template v-if="contentLang.lang === 'de'">
          <p>
            Der GenSurv Data Hub ist Teil der Forschungsinfrastruktur NUM-SAR des Netzwerks
            Universitätsmedizin (NUM). Ziel von NUM-SAR ist es, Informationen bereitzustellen sowie
            eine Infrastruktur für die Universitätsmedizin zur Verfügung zu stellen, die
            weiterführende Forschung zu Aspekten des Pandemiemanagements ermöglicht.
          </p>
          <p>
            Personen folgender Forschungseinrichtungen sind an der Gestaltung des GenSurv Data Hub
            beteiligt:
          </p>
          <ul class="institution-list mb-0">
            <li>Universitätsklinikum Tübingen, Betreiber des GenSurv Data Hub</li>
            <li>Charité - Universitätsmedizin Berlin</li>
            <li>Universitätsklinikum OWL der Universität Bielefeld</li>
            <li>Universitätsklinikum der Ruhr Universität Bochum</li>
            <li>Universitätsklinikum Düsseldorf</li>
            <li>Universitätsklinikum Freiburg</li>
            <li>Universitätsmedizin Göttingen</li>
          </ul>
        </template>
        <template v-else>
          <p>
            The GenSurv Data Hub is part of the NUM-SAR research infrastructure of the Network of
            University Medicine (NUM). The goal of NUM-SAR is to provide information and an
            infrastructure for university medical centers that enables further research into
            aspects of pandemic management.
          </p>
          <p>
            Individuals from the following research institutions are involved in the development of
            the GenSurv Data Hub:
          </p>
          <ul class="institution-list mb-0">
            <li>University Hospital Tübingen, operator of the GenSurv Data Hub</li>
            <li>Charité - University Medicine Berlin</li>
            <li>University Hospital OWL, Bielefeld University</li>
            <li>University Hospital of Ruhr University Bochum</li>
            <li>University Hospital Düsseldorf</li>
            <li>University Hospital Freiburg</li>
            <li>University Medicine Göttingen</li>
          </ul>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useContentLanguageStore } from "@/stores/contentLanguage";

const contentLang = useContentLanguageStore();
</script>

<style scoped>
/* Optional: subtle background consistency with other static pages */
.container {
  max-width: 960px;
}
</style>
