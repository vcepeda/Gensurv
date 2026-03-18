<template>
  <header>
    <nav class="navbar navbar-expand-xl navbar-dark">
      <div class="container-fluid">
        <!-- Brand -->
        <RouterLink class="navbar-brand" to="/">
          <img src="../assets/gensurv-removebg-preview.png" alt="GenSurv Logo" />
        </RouterLink>

        <!-- Toggler -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          :data-bs-target="`#${collapseId}`"
          :aria-controls="collapseId"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Collapsible content -->
        <div class="collapse navbar-collapse" :id="collapseId">
          <!-- Left nav -->
          <ul class="navbar-nav me-auto mb-0 align-items-start">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/" active-class="active" @click="closeNavbar">Home</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/upload" active-class="active" @click="closeNavbar">Data Upload</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/dashboard" active-class="active" @click="closeNavbar">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/statistics" active-class="active" @click="closeNavbar">Statistics</RouterLink>
            </li>
            <!-- <li class="nav-item">
              <RouterLink class="nav-link" to="/search" active-class="active">Search</RouterLink>
            </li> -->
            <li class="nav-item">
              <RouterLink class="nav-link" to="/help" active-class="active" @click="closeNavbar">Help</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/about" active-class="active" @click="closeNavbar">About</RouterLink>
            </li>
          </ul>

          <!-- Right auth nav -->
          <ul class="navbar-nav mb-0 me-3 align-items-start">
            <template v-if="auth.isAuthenticated && auth.username">
              <li class="nav-item">
                <span class="nav-link">Welcome, {{ auth.username }}!</span>
              </li>
              <li class="nav-item">
                <!-- Button styled like nav-link -->
                <button class="nav-link btn btn-link p-0" type="button" @click="onLogout">
                  Logout
                </button>
              </li>
            </template>

            <template v-else>
              <li class="nav-item">
                <RouterLink class="nav-link" to="/register" active-class="active" @click="closeNavbar">Register</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink class="nav-link" to="/login" active-class="active" @click="closeNavbar">Login</RouterLink>
              </li>
            </template>
          </ul>

          <!-- Commented out code for search functionality -->
          <!-- <form class="d-flex align-items-start mb-0" role="search" @submit.prevent="onSubmitSearch">
            <input
              v-model="query"
              class="form-control me-2"
              type="search"
              name="query"
              placeholder="Search..."
              aria-label="Search"
              style="width: 200px; height: 38px;"
            />
            <button class="btn btn-outline-primary" type="submit" style="height: 38px; padding: 0 12px;">
              <i class="fas fa-search"></i>
            </button>
          </form> -->
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
import router from "../router"
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { Collapse } from "bootstrap";

const auth = useAuthStore();
const collapseId = "navbarSupportedContent";
let collapseInstance = null;

onMounted(() => {
  const elem = document.getElementById(collapseId);
  if (elem) {
    collapseInstance = new Collapse(elem, { toggle: false });
  }
});

function closeNavbar() {
  if (collapseInstance) {
    collapseInstance.hide();
  }
}

function onLogout() {
  closeNavbar();
  auth.logout();
  router.push('/logout')
}
// Emits
const emit = defineEmits(["logout", "search"]);

// Local state
const query = ref("");

function onSubmitSearch() {
  emit("search", query.value);
}
</script>

<style scoped>
/* This matches your old base.html global header rules.
   If you already put these in a global CSS file, you can delete them here. */

header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1050;
  width: 100%;
  padding: 0;
}

header .navbar {
  background: linear-gradient(90deg, #4b79a1 0%, #003366 100%) !important;
  padding: 10px 20px;
}

header .navbar-brand img {
  height: 50px;
}

header .nav-link {
  color: #fff !important;
  padding: 10px 15px !important;
  transition: color 0.3s ease;
}

header .nav-link:hover {
  color: #ffcc00 !important;
}

header .navbar-toggler {
  border-color: rgba(255, 255, 255, 0.5);
}

header .navbar-toggler-icon {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='rgba%28255, 255, 255, 0.85%29' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
}

header .btn-outline-primary {
  color: #fff;
  border-color: #fff;
}

header .btn-outline-primary:hover {
  background-color: #fff;
  color: #003366;
}

header .form-control {
  border: 1px solid rgba(255, 255, 255, 0.5);
}

header .form-control:focus {
  border-color: #fff;
  box-shadow: 0 0 0 0.2rem rgba(255, 255, 255, 0.25);
}

@media (max-width: 991px) {
  header .navbar-nav {
    align-items: flex-start !important;
  }
}

/* Optional: make the logout button look exactly like a link */
button.nav-link {
  text-decoration: none;
}
button.nav-link:focus {
  outline: none;
  box-shadow: none;
}
</style>
