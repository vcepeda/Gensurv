<template>
  <aside class="sidebar-right">
    <div class="sidebar-header" role="button" tabindex="0" @click="toggleSidebar"
         :aria-expanded="sidebarOpen" id="sidebarHeader">
      <h5><i class="bi bi-list-ul"></i> On this page</h5>
      <i class="bi bi-chevron-down sidebar-toggle-icon"></i>
    </div>

    <nav class="sidebar-nav" :class="{ show: sidebarOpen }" id="sidebarNav">
      <!-- Home menu -->
      <li id="home-menu" class="menu-item" v-show="visibleMenu === 'home-menu' || visibleMenu === 'all'">
        <a href="#overview" @click.prevent="scrollToSection" class="d-flex align-items-center">
          <i class="bi bi-house-door me-2"></i> GenSurv Overview
        </a>
        <ul>
          <li><a href="#num" @click.prevent="scrollToSection">Network of University Medicine</a></li>
          <li><a href="#publications" @click.prevent="scrollToSection">Publications</a></li>
          <li><a href="#pipelines" @click.prevent="scrollToSection">Bioinformatics Pipelines</a></li>
          <li><a href="#collaborators" @click.prevent="scrollToSection">Collaborator Websites</a></li>
        </ul>
      </li>

      <!-- Upload menu (authenticated only) -->
      <li id="upload-menu" class="menu-item" v-if="isAuthenticated" v-show="visibleMenu === 'upload-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/upload')" class="d-flex align-items-center">
          <i class="bi bi-cloud-upload me-2"></i> Data Upload
        </a>
        <ul>
          <li><a href="#single-upload" @click.prevent="scrollToSection">Single Sample Upload</a></li>
          <li><a href="#bulk-upload" @click.prevent="scrollToSection">Bulk Upload</a></li>
        </ul>
      </li>

      <!-- Samples menu (authenticated only) -->
      <li id="samples-menu" class="menu-item" v-if="isAuthenticated" v-show="visibleMenu === 'samples-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/samples')" class="d-flex align-items-center">
          <i class="bi bi-file-earmark-text me-2"></i> View Samples
        </a>
        <ul>
          <li><a href="#sample1" @click.prevent="scrollToSection">Sample 1</a></li>
          <li><a href="#sample2" @click.prevent="scrollToSection">Sample 2</a></li>
        </ul>
      </li>

      <!-- Analyses menu (authenticated only) -->
      <li id="analyses-menu" class="menu-item" v-if="isAuthenticated" v-show="visibleMenu === 'analyses-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/dashboard')" class="d-flex align-items-center">
          <i class="bi bi-graph-up me-2"></i> Analyses
        </a>
        <ul>
          <li><a href="#" @click.prevent="navigateTo('/dashboard')">Submissions Dashboard</a></li>
        </ul>
      </li>

      <!-- Sample Results menu -->
      <li id="sample-menu" class="menu-item" v-if="showSampleMenu" v-show="visibleMenu === 'sample-menu' || visibleMenu === 'all'" :class="{ active: isSamplePage }">
        <a href="#" @click.prevent="navigateTo(samplePath)" class="d-flex align-items-center">
          <i class="bi bi-clipboard-data me-2"></i> Sample Results
        </a>
        <ul>
          <li><a href="#bac" @click.prevent="scrollToSection">Basic Bacterial Analyses</a></li>
          <li><a href="#plas" @click.prevent="scrollToSection">Plasmid-Related Analyses</a></li>
          <li><a href="#" @click.prevent="navigateTo(samplePathDetailed)">Detailed Results</a></li>
        </ul>
      </li>

      <!-- Search menu -->
      <li id="search-menu" class="menu-item" v-show="visibleMenu === 'search-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/search')" class="d-flex align-items-center">
          <i class="bi bi-search me-2"></i> Sample Search
        </a>
      </li>

      <!-- Help menu -->
      <li id="help-menu" class="menu-item" v-show="visibleMenu === 'help-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/help')" class="d-flex align-items-center">
          <i class="bi bi-question-circle me-2"></i> Help
        </a>
        <ul>
          <li><a href="#single-upload" @click.prevent="scrollToSection">Single Sample Upload</a></li>
          <li><a href="#bulk-upload" @click.prevent="scrollToSection">Bulk Upload</a></li>
          <li><a href="#details" @click.prevent="scrollToSection">Detailed Metadata Information</a></li>
        </ul>
      </li>

      <!-- About menu -->
      <li id="about-menu" class="menu-item" v-show="visibleMenu === 'about-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/about')" class="d-flex align-items-center">
          <i class="bi bi-info-circle me-2"></i> About
        </a>
        <ul>
          <li><a href="#team" @click.prevent="scrollToSection">Our Team</a></li>
          <li><a href="#mission" @click.prevent="scrollToSection">Mission Statement</a></li>
        </ul>
      </li>

      <!-- Research menu -->
      <li id="research-menu" class="menu-item" v-show="visibleMenu === 'research-menu' || visibleMenu === 'all'">
        <a href="#" @click.prevent="navigateTo('/research')" class="d-flex align-items-center">
          <i class="bi bi-journal-medical me-2"></i> Research
        </a>
        <ul>
          <li><a href="#pub" @click.prevent="scrollToSection">Our Publications</a></li>
          <li><a href="#rela" @click.prevent="scrollToSection">Related Publications</a></li>
        </ul>
      </li>
    </nav>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const sidebarOpen = ref(false)
const visibleMenu = ref('home-menu')
const isAuthenticated = ref(false) // Get from store/auth

// Sample page state
const showSampleMenu = ref(false)
const isSamplePage = computed(() => route.name === 'sample-results' || route.name === 'sample-all-results')
const samplePath = computed(() => `/submission/${route.params.submissionId}/sample/${route.params.sampleId}`)
const samplePathDetailed = computed(() => `/submission/${route.params.submissionId}/sample/${route.params.sampleId}/detailed`)

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const navigateTo = async (path) => {
  await router.push(path)
  closeSidebar()
}

const scrollToSection = (event) => {
  const href = event.target.getAttribute('href')
  const targetId = href.split('#')[1]
  if (targetId) {
    const element = document.getElementById(targetId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      element.scrollTop -= 100
      if (window.innerWidth < 992) {
        closeSidebar()
      }
    }
  }
}

// Watch route to determine which menu to show
watch(
  () => route.path,
  () => {
    if (route.path.includes('/upload')) {
      visibleMenu.value = 'upload-menu'
    } else if (route.path.includes('/dashboard')) {
      visibleMenu.value = 'analyses-menu'
    } else if (route.path.includes('/search')) {
      visibleMenu.value = 'search-menu'
    } else if (route.path.includes('/help')) {
      visibleMenu.value = 'help-menu'
    } else if (route.path.includes('/about')) {
      visibleMenu.value = 'about-menu'
    } else if (route.path.includes('/research')) {
      visibleMenu.value = 'research-menu'
    } else if (route.path.match(/\/submission\/\d+\/sample\//)) {
      visibleMenu.value = 'sample-menu'
      showSampleMenu.value = true
    } else {
      visibleMenu.value = 'home-menu'
    }
  },
  { immediate: true }
)

// Setup Intersection Observer for active link highlighting
watch(
  () => route.path,
  () => {
    setupObserver()
  },
  { immediate: true }
)

const setupObserver = () => {
  const observerOptions = { root: null, rootMargin: '-20% 0px -35% 0px', threshold: 0 }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id')
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
          link.classList.remove('active')
          const href = link.getAttribute('href') || ''
          if (href.includes('#' + id)) link.classList.add('active')
        })
      }
    })
  }, observerOptions)

  document.querySelectorAll('main [id]').forEach(section => {
    if (section) observer.observe(section)
  })
}
</script>

<style scoped>
.sidebar-right {
  position: fixed;
  right: 0;
  top: var(--nav-h);
  width: var(--right-w);
  height: calc(100vh - var(--nav-h));
  overflow-y: auto;
  background: #fff;
  border-left: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
  box-sizing: border-box;
}

.sidebar-header {
  background: linear-gradient(135deg, #4b79a1 0%, #003366 100%);
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar-header:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.sidebar-header h5 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sidebar-toggle-icon {
  transition: transform 0.3s ease;
  display: none;
}

.sidebar-nav {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav li {
  margin-bottom: 0.5rem;
}

.sidebar-nav a {
  display: block;
  padding: 0.5rem 0.75rem;
  color: #495057;
  text-decoration: none;
  border-left: 3px solid transparent;
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.sidebar-nav a:hover {
  background-color: #f8f9fa;
  color: #003366;
  border-left-color: #4b79a1;
  padding-left: 1rem;
}

.sidebar-nav a.active {
  background-color: #e7f1ff;
  color: #003366;
  border-left-color: #003366;
  font-weight: 500;
}

.sidebar-nav ul {
  list-style: none;
  padding-left: 1.25rem;
  margin-top: 0.5rem;
}

.sidebar-nav ul a {
  font-size: 0.85rem;
  padding: 0.4rem 0.75rem;
}

@media (max-width: 991px) {
  .sidebar-right {
    display: none;
  }

  .sidebar-toggle-icon {
    display: block;
  }

  .sidebar-nav {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .sidebar-nav.show {
    max-height: 70vh;
    overflow-y: auto;
    padding-bottom: 1rem;
  }

  .sidebar-header[aria-expanded="true"] .sidebar-toggle-icon {
    transform: rotate(180deg);
  }
}
</style>
