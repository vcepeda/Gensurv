<template>
  <footer class="site-footer">
    <div class="container">
      <div class="row align-items-center justify-content-between">
        <!-- Left logos -->
        <div class="col-md-4 text-center text-md-start mb-3 mb-md-0">
          <img src="../assets/NUM_u_BMBF_Querformat_en.jpg"
               alt="NUM / BMBF"
               class="img-fluid"
               style="max-height: 120px;">
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
</style>