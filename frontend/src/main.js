import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import apiClient from './api/client'
import App from './App.vue'
import './style.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

async function bootstrap() {
  await apiClient.get('/api/csrf/')

  const app = createApp(App)

  app.config.globalProperties.$axios = apiClient

  app.use(createPinia())
  app.use(router)

  app.mount('#app')
}

bootstrap()
