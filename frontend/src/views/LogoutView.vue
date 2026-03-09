<template>
  <div class="container mt-5 text-center">
    <h2>You have been logged out successfully.</h2>
    <p>We hope to see you back soon!</p>

    <router-link to="/login" class="btn btn-primary me-2">Login Again</router-link>
    <router-link to="/" class="btn btn-secondary">Back to Home</router-link>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { logout } from "@/api/auth";

onMounted(async () => {
  await logout();
});
</script>
