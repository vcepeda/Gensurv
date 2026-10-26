<template>
  <footer class="site-footer">
    <div class="container">
      <div class="row align-items-center justify-content-between">
        <!-- Left logos -->
        <div class="col-md-5 text-center text-md-start mb-3 mb-md-0">
          <div class="footer-logo-panel">
            <img src="../assets/NUM-LOGO-POS-EN-RGB.png"
                 alt="NUM - Network of University Medicine"
                 class="img-fluid footer-logo">
            <img src="../assets/BMFTR_de_DTP_CMYK_gef_durch.png"
                 alt="Gefördert durch: Bundesministerium für Forschung, Technologie und Raumfahrt"
                 class="img-fluid footer-logo">
            <p class="footer-fkz mb-0">Funding reference number (FKZ): 01KX2524</p>
          </div>
        </div>

        <!-- Right text + links -->
        <div class="col-md-7 text-center text-md-end">
          <p class="footer-copy mb-2">
            © 2024 University Hospital and Faculty of Medicine Tübingen
          </p>

          <p class="footer-links mb-0">
            <router-link to="/impressum">Impressum</router-link> |
            <router-link to="/contact">Contact</router-link> |
            <router-link to="/privacy">Privacy Policy</router-link> |
            <router-link to="/accessibility">Accessibility</router-link>
          </p>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
// No logic needed for footer
</script>

<style scoped>
footer {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  background: linear-gradient(105deg, #48ac9f 0%, #467f7b 16%, #43b8a7 38%, #3dcbb5 59%, #46968c 100%);
  color: white;
  padding: 2.5rem 0;
  margin-top: auto;
  border: 0;
  border-radius: 0;
}

footer::before,
footer::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}

footer::before {
  background: rgb(75 192 174 / 65%);
  clip-path: polygon(16.5% 0, 79% 0, 81% 100%, 13.5% 100%);
}

footer::after {
  background: rgb(54 216 190 / 38%);
  clip-path: polygon(33.3% 0, 65% 0, 62% 100%, 35% 100%);
}

footer .footer-copy,
footer .footer-links {
  color: white;
}

footer .footer-links a {
  color: white;
  text-decoration: none;
  transition: color 0.3s ease;
}

footer .footer-links a:hover,
footer .footer-links a:focus-visible {
  color: white;
  text-decoration: underline;
  text-underline-offset: 0.2em;
}

.footer-logo-panel {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  background: #ffffff;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.footer-logo {
  max-height: 60px;
  width: auto;
}

.footer-fkz {
  width: 100%;
  color: var(--num-slate);
  font-size: 0.75rem;
}
</style>
