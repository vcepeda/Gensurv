# Django to Vue Components Migration Guide

## Overview
Your Django `base.html` has been split into reusable Vue components with the same styling and functionality.

## Components Created

### 1. **Navbar.vue** (`src/components/Navbar.vue`)
- Header navigation with logo, links, and search
- Responsive toggle menu for mobile
- Authentication state display
- Search functionality with router integration
- Integrates all navbar styling from base.html

### 2. **Banner.vue** (`src/components/Banner.vue`)
- Maintenance and help alert banners
- Conditional display based on route
- Smooth fade transitions

### 3. **Sidebar.vue** (`src/components/Sidebar.vue`)
- Right sidebar with navigation menu
- Context-aware menu display based on current page
- Intersection observer for active link highlighting
- Mobile-responsive collapsible menu
- All sections: Home, Upload, Samples, Analyses, Sample Results, Search, Help, About, Research

### 4. **Footer.vue** (`src/components/Footer.vue`)
- Footer with logo and links
- Copyright and navigation links
- Responsive layout matching original design

### 5. **App.vue** (Updated)
- Main layout wrapper
- Composes all components
- Contains global styles and CSS custom properties
- Router view for page content

## Setup Instructions

### 1. Install Required Dependencies
```bash
npm install
npm install vue-router pinia  # Add if not already installed
```

### 2. Create Router Configuration
Create `src/router/index.js`:

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../pages/Home.vue') },
  { path: '/upload', name: 'upload', component: () => import('../pages/Upload.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('../pages/Dashboard.vue') },
  { path: '/search', name: 'search', component: () => import('../pages/Search.vue') },
  { path: '/help', name: 'help', component: () => import('../pages/Help.vue') },
  { path: '/about', name: 'about', component: () => import('../pages/About.vue') },
  { path: '/research', name: 'research', component: () => import('../pages/Research.vue') },
  { path: '/contact', name: 'contact', component: () => import('../pages/Contact.vue') },
  { path: '/impressum', name: 'impressum', component: () => import('../pages/Impressum.vue') },
  { path: '/privacy', name: 'privacy', component: () => import('../pages/Privacy.vue') },
  { path: '/accessibility', name: 'accessibility', component: () => import('../pages/Accessibility.vue') },
  { path: '/login', name: 'login', component: () => import('../pages/Login.vue') },
  { path: '/register', name: 'register', component: () => import('../pages/Register.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

### 3. Setup Authentication Store (Pinia)
Create `src/stores/auth.js`:

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isAuthenticated = computed(() => !!user.value)
  const username = computed(() => user.value?.username || '')

  async function fetchUser() {
    try {
      const response = await axios.get('/api/user/')
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
    }
  }

  async function logout() {
    try {
      await axios.post('/api/logout/')
    } catch (error) {
      console.error('Logout error:', error)
    }
    user.value = null
  }

  return { user, isAuthenticated, username, fetchUser, logout }
})
```

### 4. Update main.js
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
```

### 5. Update index.html
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GenSurv</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
```

### 6. Update package.json (if needed)
```json
{
  "dependencies": {
    "vue": "^3.5.24",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "bootstrap": "^5.3.0",
    "bootstrap-icons": "^1.11.0",
    "axios": "^1.6.0"
  }
}
```

## Key Changes from Django Template

| Django Feature | Vue Equivalent |
|---|---|
| `{% url 'home' %}` | `router-link` / `router.push()` |
| `{% if user.is_authenticated %}` | `isAuthenticated` computed property |
| `{% block content %}` | `<router-view />` |
| URL reversing | Vue Router with named routes |
| Static files | Update paths in component props |
| Template tags | Vue directives (`v-if`, `v-for`, etc.) |

## Integration with Django Backend

### Update Static File Paths
- Replace `{% static 'path/to/file' %}` with `/api/static/path/to/file`
- Or configure a proxy in `vite.config.js`

### API Integration
Create `src/api/client.js`:
```javascript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add request interceptor for auth token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

## Notes

- User authentication data is referenced but needs to be connected to your auth store
- Search functionality routes to `/search` - adjust based on your backend API
- Banner messages should be managed through your app state or API
- The sidebar uses Intersection Observer for scroll-based active link highlighting
- All styling is scoped to components to avoid CSS conflicts

## Next Steps

1. Create page components for each route in `src/pages/`
2. Set up your auth store with actual API calls
3. Update API URLs to match your backend
4. Add any missing dependencies to package.json
5. Test routing and component rendering
