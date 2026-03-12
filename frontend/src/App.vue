<template>
  <div class="app-root" id="app-scroll">
    <!-- Banner sits below the fixed navbar (same as old base.html) -->
    <!-- <Banner
      v-if="banner"
      :type="banner.type"
      :message="banner.message"
      :navHeight="navHeight"
    /> -->

    <!-- Fixed header -->
    <Navbar
      :user="auth"
      :navHeight="navHeight"
      @logout="handleLogout"
      @search="handleSearch"
    />

    <!-- Main layout -->
    <div class="app-shell">
      <main class="container app-main">
        <RouterView />
      </main>

      <!-- Right sidebar (optional) -->
      <!-- <Sidebar
        v-if="showSidebar"
        class="app-sidebar"
        :navHeight="navHeight"
        :activeMenu="activeMenu"
        :isAuthenticated="auth.isAuthenticated"
      /> -->
    </div>

    <!-- Footer full width -->
    <Footer />
  </div>
</template>

<!-- <script setup>
import "./style.css";
import { ref, reactive, computed, onMounted, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";

import Banner from "./components/Banner.vue";
import Navbar from "./components/Navbar.vue";
import Sidebar from "./components/Sidebar.vue";
import Footer from "./components/Footer.vue";

import { me, logout } from "./api/auth";

const router = useRouter();
const route = useRoute();

const navHeight = 70;

const auth = reactive({
  isAuthenticated: false,
  username: null,
});

const banner = ref(null);



const showSidebar = computed(() => {
  // hide on mobile via CSS anyway, but you can also hide on certain pages:
  const noSidebarRoutes = new Set(["login", "register"]);
  return !noSidebarRoutes.has(route.name);
});

// Decide which sidebar menu to show (replacement for your old URL-matching JS)
const activeMenu = ref("home-menu");

function computeActiveMenu(r) {
  const p = r.path || "";

  if (p.startsWith("/upload")) return "upload-menu";
  if (p.startsWith("/dashboard")) return "analyses-menu";
  if (p.startsWith("/statistics")) return "analyses-menu";
  if (p.startsWith("/search") || p.startsWith("/dashboard_and_search")) return "search-menu";
  if (p.startsWith("/help")) return "help-menu";
  if (p.startsWith("/about")) return "about-menu";
  if (p.startsWith("/research")) return "research-menu";
  // sample results example, adapt to your actual Vue route paths:
  if (p.match(/\/submission\/\d+\/sample\/[^/]+/)) return "sample-menu";

  return "home-menu";
}

watch(
  () => route.fullPath,
  async () => {
    activeMenu.value = computeActiveMenu(route);
    // Wait for Vue to finish rendering before scrolling
    await nextTick();
    // Scroll both window and document to top
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  },
  { immediate: false }
);

onMounted(async () => {
  // Ask backend who is logged in (replaces Django template user.is_authenticated)
  try {
    const data = await me();
    console.log("ME RESPONSE:", data);
    auth.isAuthenticated = !!data?.is_authenticated;
    auth.username = data?.username ?? null;
    // console.log("username is: ",auth.username)
  } catch {
    auth.isAuthenticated = false;
    auth.username = null;
  }
});

async function handleLogout() {
  await logout();
  auth.isAuthenticated = false;
  auth.username = null;
  router.push("/login");
}

// Navbar emits a search string → route to search page with query param
function handleSearch(query) {
  router.push({ path: "/search", query: { query } });
}
</script> -->


<script setup>
import "./style.css";
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";

import Navbar from "./components/Navbar.vue";
import Sidebar from "./components/Sidebar.vue";
import Footer from "./components/Footer.vue";

import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const route = useRoute();

const navHeight = 70;
const auth = useAuthStore();

onMounted(() => {
  auth.fetchUser();
});

const showSidebar = computed(() => {
  const noSidebarRoutes = new Set(["login", "register"]);
  return !noSidebarRoutes.has(route.name);
});


const activeMenu = ref("home-menu");

function computeActiveMenu(r) {
  const p = r.path || "";

  if (p.startsWith("/upload")) return "upload-menu";
  if (p.startsWith("/dashboard")) return "analyses-menu";
  if (p.startsWith("/search") || p.startsWith("/dashboard_and_search")) return "search-menu";
  if (p.startsWith("/help")) return "help-menu";
  if (p.startsWith("/about")) return "about-menu";
  if (p.startsWith("/research")) return "research-menu";
  if (p.match(/\/submission\/\d+\/sample\/[^/]+/)) return "sample-menu";

  return "home-menu";
}

watch(
  () => route.fullPath,
  async () => {
    activeMenu.value = computeActiveMenu(route);
    await nextTick();
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }
);


async function handleLogout() {
  await auth.logout();
  router.push("/login");
}

function handleSearch(query) {
  router.push({ path: "/search", query: { query } });
}
</script>


<style>
/* Layout: main + fixed sidebar, footer stays at bottom */
.app-shell {
  min-height: calc(100vh - var(--nav-h));
}

/* keep your old main spacing behavior */
.app-main {
  padding: 0.75rem 1rem 2rem;
}

/* If your Sidebar component is already position:fixed you can omit this. */
.app-sidebar {
  /* optional */
}

@media (max-width: 991px) {
  /* Sidebar hidden on mobile */
  .app-sidebar {
    display: none;
  }
}
</style>
