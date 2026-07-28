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
  width: 100%;
  box-sizing: border-box;
  background: linear-gradient(90deg, var(--num-slate) 0%, var(--num-slate-dark) 100%);
  color: white;
  padding: 2.5rem 0;
  margin-top: auto;
  border-width: 4px 0 0 0;
  border-style: solid;
  border-image: linear-gradient(
      90deg,
      var(--num-aqua) 0%,
      var(--num-gold) 50%,
      var(--num-rose) 100%
    )
    1;
}

footer .footer-copy,
footer .footer-links {
  color: white;
}

footer .footer-links a {
  color: var(--num-rose);
  text-decoration: none;
  transition: color 0.3s ease;
}

footer .footer-links a:hover {
  color: #f27f8d;
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
