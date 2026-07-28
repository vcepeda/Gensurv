<template>
  <div class="container mt-5 mb-5">
    <div class="mb-4 text-center">
      <h1 class="mb-2">{{ page.title }}</h1>
      <p v-if="page.subtitle" class="text-muted mb-0">{{ page.subtitle }}</p>
    </div>

    <!-- Page body -->
    <div class="card shadow-sm">
      <div class="card-body p-4">
        <!-- IMPORTANT: v-html assumes content is trusted (it is, since it's your own static pages) -->
        <div v-html="page.html"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useContentLanguageStore } from "@/stores/contentLanguage";

const route = useRoute();
const contentLang = useContentLanguageStore();

/**
 * One source-of-truth for static content.
 * You can keep it here, or move this object into `src/content/staticPages.js`
 */
const PAGES_EN = {
  impressum: {
    title: "Impressum",
    subtitle: null,
    html: `
      <section class="mt-2">
        <h2>Responsible Party</h2>
        <p>
          University Hospital Tübingen (UKT)<br>
          Eberhard Karls University Tübingen<br>
          Faculty of Medicine<br>
          Geissweg 5/1<br>
          72076 Tübingen<br>
          Germany
        </p>
        <p>
          Phone: +49 7071 29-0<br>
          Email: <a href="mailto:info@medizin.uni-tuebingen.de">info@medizin.uni-tuebingen.de</a><br>
          Website: <a href="https://www.medizin.uni-tuebingen.de" target="_blank" rel="noopener">www.medizin.uni-tuebingen.de</a>
        </p>
      </section>

      <section class="mt-4">
        <h2>Legal Information</h2>
        <p>
          University Hospital Tübingen is a public corporation.<br>
          It is represented by the Chief Medical Director and the Commercial Director.
        </p>
      </section>

      <section class="mt-4">
        <h2>Disclaimer</h2>
        <h3>Content Accountability</h3>
        <p>
          The content of our pages has been prepared with great care. However, we cannot guarantee the accuracy,
          completeness, or timeliness of the content. As a service provider, we are responsible for our own content
          on these pages in accordance with general laws. However, we are not obliged to monitor transmitted or stored
          external information or to investigate circumstances indicating illegal activity (§§ 8–10 TMG).
          Obligations to remove or block the use of information under general laws remain unaffected. However, liability
          in this respect is only possible from the time of knowledge of a specific infringement. Upon notification of such
          violations, we will remove this content immediately.
        </p>

        <h3>External Links</h3>
        <p>
          Our website contains links to external websites of third parties over whose content we have no control.
          Therefore, we cannot accept any liability for this external content. The respective provider or operator of the pages
          is always responsible for the content of the linked pages. The linked pages were checked for possible legal violations
          at the time of linking. Illegal content was not recognizable at the time of linking. However, permanent monitoring of
          the content of the linked pages is not reasonable without concrete evidence of a violation. If we become aware of any
          legal violations, we will remove such links immediately.
        </p>
      </section>

      <section class="mt-4">
        <h2>Contact Information</h2>
        <p>
          If you have any questions regarding this Impressum, please contact:<br>
          <strong>University Hospital Tübingen</strong><br>
          Phone: +49 7071 29-0<br>
          Email: <a href="mailto:info@medizin.uni-tuebingen.de">info@medizin.uni-tuebingen.de</a>
        </p>
      </section>
    `,
  },

  contact: {
    title: "Contact Us",
    subtitle:
      "We are here to assist you. Feel free to reach out to us through the following contact information or use the form below.",
    html: `
      <div class="row mt-3">
        <div class="col-md-6">
          <h3>Contact Information</h3>
          <p>
            <strong>University Hospital Tübingen</strong><br>
            Geissweg 3<br>
            72076 Tübingen<br>
            Germany<br>
          </p>
          <p>
            Email:
            <a href="mailto:Victoria.Paz.Cepeda-Espinoza@med.uni-tuebingen.de">
              Victoria.Paz.Cepeda-Espinoza@med.uni-tuebingen.de
            </a>
          </p>
          <p><strong>Office Hours:</strong> Monday to Friday, 9 AM - 5 PM</p>
        </div>

        <div class="col-md-6">
          <h3>Find Us</h3>
          <iframe
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3142.7747602915364!2d9.042848015318756!3d48.52365577925869!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x4799f3f1ec35e9ad%3A0xb2b56b0aaee6da1b!2sGeissweg%203%2C%2072076%20T%C3%BCbingen%2C%20Germany!5e0!3m2!1sen!2sde!4v1702217743952!5m2!1sen!2sde"
            width="100%"
            height="250"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade">
          </iframe>
        </div>
      </div>
    `,
  },

  privacy: {
    title: "Privacy Statement",
    subtitle: "Status: 17.11.2021",
    html: `
      <section class="mt-2">
        <p>
          Data protection and data security for the customers and partners of the University Hospital and the Medical Faculty
          Tübingen, as well as for interested parties and users of our website, have a high priority in our clinic.
          Transparency regarding the processing of your personal data, as well as the protection of your data, are therefore
          particularly important to us.
        </p>
        <p>
          With this declaration, we give you an overview of how your personal data is collected and processed when you use our
          website and what you can do yourself to better protect your data.
        </p>
      </section>

      <section class="mt-4">
        <h2>Contact Data Protection Officer</h2>
        <h3>Responsible for Processing</h3>
        <p>
          <strong>University Hospital Tübingen</strong><br>
          Geissweg 3<br>
          72076 Tübingen<br>
          Phone: +49 7071 29-0
        </p>

        <h3>Data Protection Officer</h3>
        <p>
          <strong>Sven Sender</strong><br>
          Geissweg 3<br>
          72076 Tübingen<br>
          Phone: +49 7071 29-87667<br>
          Email: <a href="mailto:dsb@med.uni-tuebingen.de">dsb@med.uni-tuebingen.de</a>
        </p>
      </section>
    `,
  },

  accessibility: {
    title: "Accessibility Statement",
    subtitle: null,
    html: `
      <p class="lead">
        In compliance with Section 10 Paragraph 1 of the State Disability Equality Act, the University Hospital
        and Medical Faculty of the Eberhard Karls University of Tübingen works to make its website accessible without obstacles (L-BGG).
      </p>

      <p>
        This accessibility statement applies to the main UKT website at:
        <a href="https://www.medizin.uni-tuebingen.de/de/" target="_blank" rel="noopener">
          https://www.medizin.uni-tuebingen.de/de/
        </a>
      </p>

      <h2>Status of Compatibility with the Requirements</h2>
      <p>This website is only partially compatible with Section 10(1) of the L-BGG due to the following incompatibilities:</p>

      <h3>Non-Accessible Content</h3>
      <p>The content listed below is not accessible for the following reasons:</p>

      <h4>a) Incompatibility with Section 10(1) L-BGG</h4>
      <h4>a) Incompatibility with Section 10(1) L-BGG</h4>
    <ul>
        <li>BITV 9.1.1.1 a: Several control elements lack alternate texts</li>
        <li>BITV 9.1.1.1 b: A few incorrect and many missing alternative texts for graphics</li>
        <li>BITV 9.1.1.1 c: Layout components are not used with empty alt attributes</li>
        <li>BITV 9.1.2.3: Missing audio description or full text alternative for videos</li>
        <li>BITV 9.1.2.5: Missing audio description for videos</li>
        <li>BITV 9.1.3.1 a: Incorrectly used HTML structural elements for headings</li>
        <li>BITV 9.1.3.1 b: No correct HTML structure elements for lists</li>
        <li>BITV 9.1.3.1 d: Structural elements are not correctly used to structure the content</li>
        <li>BITV 9.1.3.1 d: For layout tables, no structural markup is used</li>
        <li>BITV 9.1.3.1 e: Form element labeling cannot be determined programmatically</li>
        <li>BITV 9.1.3.5: User data entry fields do not indicate their intended use</li>
        <li>BITV 9.1.4.1: Not entirely usable without colors</li>
        <li>BITV 9.1.4.3: Contrasts of texts not sufficient in the ratio 1:4.5</li>
        <li>BITV 9.1.4.5: Partial use of font graphics</li>
        <li>BITV 9.1.4.11: Contrasts for graphics and graphic control elements insufficient (1:3)</li>
        <li>BITV 9.1.4.13: Faded-in contents partly not operable</li>
        <li>BITV 9.2.2.2: Moving content cannot be switched off</li>
        <li>BITV 9.2.4.7: Current position of focus partly not clear</li>
        <li>BITV 9.2.5.3: Visible caption not always part of accessible name</li>
        <li>BITV 9.3.1.1: Main language not indicated on some pages</li>
        <li>BITV 9.3.1.2: Other language not marked</li>
        <li>BITV 9.3.2.3: Navigation inconsistent on a few pages</li>
        <li>BITV 9.3.3.1: Insufficient error detection</li>
        <li>BITV 12.1.1: Missing documentation of compatibility and accessibility</li>
    </ul>
    <p>Additionally, all PDFs included on the website are not accessible according to the PAC standard.</p>
    <p>There is a lack of description in plain language and, if applicable, a variant in sign language.</p>

    <h4>b) Disproportionate Burden</h4>
    <p>The barrier-free implementation of the PDFs contained on the website and the creation of the discussion in plain language currently represent a disproportionate burden. They are therefore an exception.</p>

    <h4>c) Content Outside Applicable Legislation</h4>
    <p>A version in sign language is not mandatory.</p>
    `,
  },
};

// German versions. Impressum/Privacy/Accessibility reference German law
// (TMG, L-BGG, BITV) and need an official source, not a free translation -
// falling back to the English text until that's provided. Only Contact
// (plain address/map info, no legal text) is translated for now.
const PAGES_DE = {
  impressum: {
    title: "Impressum",
    subtitle: null,
    html: `
      <section class="mt-2">
        <h2>Anbieter der Seiten unter der Domain</h2>
        <p>
          <strong>Universitätsklinikum Tübingen</strong><br>
          Rechtsfähige Anstalt des öffentlichen Rechts der Universität Tübingen gemäß § 1 Abs. 1 Nr. 3 UKG (Universitätsklinika-Gesetz)
        </p>
        <p>
          Geissweg 3<br>
          72076 Tübingen
        </p>
        <p>
          E-Mail: <a href="mailto:service@med.uni-tuebingen.de">service@med.uni-tuebingen.de</a><br>
          Website: <a href="https://www.medizin.uni-tuebingen.de" target="_blank" rel="noopener">www.medizin.uni-tuebingen.de</a>
        </p>
        <p>
          Institutskennzeichen: IK 260 840 108<br>
          Steuer-Nr.: 86156/09402<br>
          USt-ID: DE 146 889 674
        </p>
        <p>
          Universitätsklinikum Tübingen wird vertreten durch den Vorstand des Klinikums.
        </p>
      </section>

      <section class="mt-4">
        <h2>Kontakt</h2>
        <p>
          Vorstand des Universitätsklinikums Tübingen<br>
          Geissweg 3<br>
          72076 Tübingen
        </p>
        <p>
          Telefon: 07071 29-0<br>
          Fax: 07071 29-3966<br>
          E-Mail: <a href="mailto:vorstand@med.uni-tuebingen.de">vorstand@med.uni-tuebingen.de</a>
        </p>
      </section>

      <section class="mt-4">
        <h3>Mitglieder des Vorstands</h3>
        <p>
          Prof. Dr. med. Jens Maschmann<br>
          Leitender Ärztlicher Direktor und Vorstandsvorsitzender
        </p>
        <p>
          Dipl.-Volkswirtin Dr. Daniela Harsch<br>
          Kaufmännische Direktorin und Stellvertretende Vorstandsvorsitzende
        </p>
        <p>
          Prof. Dr. med. Ulrike Ernemann<br>
          Stellvertretende Leitende Ärztliche Direktorin
        </p>
        <p>
          Prof. Dr. med. Sara Y. Brucker<br>
          Dekanin der Medizinischen Fakultät
        </p>
        <p>
          Dipl.-Kfm. Klaus Tischler<br>
          Pflegedirektor
        </p>
      </section>

      <section class="mt-4">
        <h3>Aufsichtsbehörde</h3>
        <p>
          Dr. Hans J. Reiter<br>
          Vorsitzender<br>
          Ministerialdirektor
        </p>
      </section>

      <section class="mt-4">
        <h3>Ärztekammern</h3>
        <p>
          Folgende Links führen zu den relevanten Kammern und dem Berufsrecht der Mitarbeiter und Mitarbeiterinnen des Klinikums.
        </p>
        <ul>
          <li>Landesärztekammer Baden-Württemberg, Berufsordnung</li>
          <li>Zahnärztekammer Baden-Württemberg, Berufsrecht</li>
          <li>Landesapothekerkammer Baden-Württemberg, Berufsordnung</li>
          <li>Landespsychotherapeutenkammer Baden-Württemberg</li>
        </ul>
        <p>
          Soweit andere Berufe im Sinne von § 5 Abs. 1 Nr. 5 Telemediengesetz individuell Tele- oder Mediendienste im Rahmen ihrer Berufsausübung anbieten oder erbringen, ist dies beim jeweiligen Angebot vermerkt. Dies gilt auch für Berufsbezeichnungen, die nicht in Deutschland verliehen wurden.
        </p>
      </section>

      <section class="mt-4">
        <h2>Urheberrecht &amp; Haftungsausschluss</h2>
        <h3>Externe Links</h3>
        <p>
          Der Internetauftritt des Universitätsklinikums Tübingen enthält auch Links oder Verweise auf Websites Dritter. Durch den Link vermittelt das Universitätsklinikum Tübingen lediglich den Zugang zur Nutzung dieser Inhalte. Eine Zustimmung zu den Inhalten den verlinkten Seiten Dritter ist damit nicht verbunden. Das Universitätsklinikum Tübingen übernimmt daher keine Verantwortung für die Verfügbarkeit oder den Inhalt solcher Websites und keine Haftung für Schäden oder Verletzungen, die aus der Nutzung – gleich welcher Art – solcher Inhalte entstehen. Hierfür haftet allein der Anbieter der jeweiligen Seite.
        </p>
        <p>
          Bei der erstmaligen Verknüpfung mit einem anderen Internetangebot hat die Redaktion dessen Inhalt daraufhin überprüft, ob durch ihn eine mögliche zivilrechtliche oder strafrechtliche Verantwortlichkeit ausgelöst wird. Dort nachträglich eingebundene Inhalte können jedoch leider nicht überprüft werden. Der Verweis auf dieses Angebot wird unverzüglich aufgehoben werden, sobald die Redaktion feststellt oder von anderen darauf hingewiesen wird, dass ein bestimmtes Angebot, zu dem ein Link bereitgestellt wurde, eine zivil- oder strafrechtliche Verantwortlichkeit auslöst.
        </p>

        <h3>Haftungsausschluss</h3>
        <p>
          Die Informationen dieses Internetauftritts wurden nach bestem Wissen und Gewissen sorgfältig zusammengestellt und geprüft. Es wird jedoch keine Gewähr – weder ausdrücklich noch stillschweigend – für die Vollständigkeit, Richtigkeit oder Aktualität sowie die jederzeitige Verfügbarkeit der bereit gestellten Informationen übernommen. Eine Haftung für Schäden, die aus der Nutzung oder Nichtnutzung der auf dieser Website angebotenen Informationen entstehen ist – soweit gesetzlich zulässig – ausgeschlossen.
        </p>

        <h3>Urheberrecht</h3>
        <p>
          Copyright (c), Universitätsklinikum Tübingen. Alle Rechte vorbehalten.
        </p>
        <p>
          Alle auf dieser Website veröffentlichten Inhalte (Layout, Texte, Bilder, Grafiken, Video- und Tondateien usw.) unterliegen dem Urheberrecht. Jede vom Urheberrechtsgesetz nicht zugelassene Verwertung bedarf vorheriger ausdrücklicher Zustimmung des Universitätsklinikums Tübingen. Dies gilt insbesondere für Vervielfältigung, Bearbeitung, Übersetzung, Einspeicherung, Verarbeitung bzw. Wiedergabe von Inhalten in Datenbanken oder anderen elektronischen Medien und Systemen. Fotokopien und Downloads von Web-Seiten für den privaten, wissenschaftlichen und nicht kommerziellen Gebrauch dürfen hergestellt werden.
        </p>
        <p>
          Das Urheberrecht für die Wort-Bild-Marke liegt ausdrücklich beim Universitätsklinikum Tübingen.
        </p>
        <p>
          Wir erlauben ausdrücklich und begrüßen das Zitieren unserer Dokumente und Webseiten sowie das Setzen von Links auf unsere Website.
        </p>

        <h3>Bildnachweis</h3>
        <p>
          Das Universitätsklinikum Tübingen bedankt sich bei allen Fotografen, die uns die freundliche Genehmigung erteilt haben, ihre Aufnahmen im Internetauftritt von Klinikum und Fakultät zu nutzen und bei allen abgebildeten Personen, die so freundlich waren, uns ihr Einverständnis dazu zu geben.
        </p>
      </section>
    `,
  },
  privacy: PAGES_EN.privacy, // TODO: replace with official German source once provided
  accessibility: PAGES_EN.accessibility, // TODO: replace with official German source once provided

  contact: {
    title: "Kontakt",
    subtitle:
      "Wir helfen Ihnen gerne weiter. Nutzen Sie die untenstehenden Kontaktdaten oder das Formular.",
    html: `
      <div class="row mt-3">
        <div class="col-md-6">
          <h3>Kontaktdaten</h3>
          <p>
            <strong>Universitätsklinikum Tübingen</strong><br>
            Geissweg 3<br>
            72076 Tübingen<br>
            Deutschland<br>
          </p>
          <p>
            E-Mail:
            <a href="mailto:Victoria.Paz.Cepeda-Espinoza@med.uni-tuebingen.de">
              Victoria.Paz.Cepeda-Espinoza@med.uni-tuebingen.de
            </a>
          </p>
          <p><strong>Sprechzeiten:</strong> Montag bis Freitag, 9 - 17 Uhr</p>
        </div>

        <div class="col-md-6">
          <h3>So finden Sie uns</h3>
          <iframe
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3142.7747602915364!2d9.042848015318756!3d48.52365577925869!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x4799f3f1ec35e9ad%3A0xb2b56b0aaee6da1b!2sGeissweg%203%2C%2072076%20T%C3%BCbingen%2C%20Germany!5e0!3m2!1sen!2sde!4v1702217743952!5m2!1sen!2sde"
            width="100%"
            height="250"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade">
          </iframe>
        </div>
      </div>
    `,
  },
};

const pageKey = computed(() => route.meta.pageKey || route.params.pageKey);
const page = computed(() => {
  const pages = contentLang.lang === "de" ? PAGES_DE : PAGES_EN;
  return pages[pageKey.value] || pages.impressum;
});
</script>
