<template>
  <transition name="fade">
    <div v-if="maintenanceMessage" class="alert alert-warning text-center fixed-top"
         style="top: var(--nav-h); z-index: 1100; width: 100%; padding: 10px; margin: 0;">
      <strong>Notice:</strong> {{ maintenanceMessage }}
    </div>
  </transition>

  <transition name="fade">
    <div v-if="helpBannerMessage" class="alert alert-info text-center fixed-top"
         style="top: var(--nav-h); z-index: 1100; width: 100%; padding: 10px; margin: 0;">
      <strong>Notice:</strong> {{ helpBannerMessage }}
    </div>
  </transition>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// These would come from your app state/config
const maintenanceMessage = ref('')
const helpBannerMessage = ref('')

// Compute if we should show padding adjustment
const showBannerPadding = computed(() => maintenanceMessage.value || helpBannerMessage.value)

// Watch for route changes to update banner
// useEffect(() => {
//   if (route.name === 'help' && helpBannerMessage.value) {
//     // Show help banner
//   } else {
//     // Hide or update as needed
//   }
// }, [route.name])
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
