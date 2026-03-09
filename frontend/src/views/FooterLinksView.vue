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

const route = useRoute();

/**
 * One source-of-truth for static content.
 * You can keep it here, or move this object into `src/content/staticPages.js`
 */
const PAGES = {
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

const pageKey = computed(() => route.meta.pageKey || route.params.pageKey);
const page = computed(() => PAGES[pageKey.value] || PAGES.impressum);
</script>
