<template>
  <div class="login-page">
    <div class="login-card card shadow-sm">
      <div class="card-body p-4">
        <h2 class="text-center mb-4">Login</h2>

        <!-- show backend error -->
        <div v-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <form @submit.prevent="onSubmit" novalidate>
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input
              v-model.trim="username"
              class="form-control"
              autocomplete="username"
              :disabled="loading"
              required
            />
          </div>

          <div class="mb-4">
            <label class="form-label">Password</label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              autocomplete="current-password"
              :disabled="loading"
              required
            />
          </div>

          <div class="d-grid">
            <button class="btn btn-success" type="submit" :disabled="loading">
              <span
                v-if="loading"
                class="spinner-border spinner-border-sm me-2"
                aria-hidden="true"
              ></span>
              Login
            </button>
          </div>

          <div class="text-center mt-3">
            <a href="/password_reset/">Forgot your password?</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login as apiLogin } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = "";
  loading.value = true;

  try {
    const res = await apiLogin(username.value, password.value);
    await auth.fetchUser(); 
    
    if (!auth.isAuthenticated) {
      throw new Error("Login succeeded but session not detected");
    }
    const nextPath = router.currentRoute.value.query.next || "/";
    router.push(nextPath);
  } catch (e) {
    const status = e?.response?.status;
    const data = e?.response?.data;
    password.value = "";
    
    if (data?.detail) {
      error.value = data.detail;
    } else if (data?.errors?.__all__?.[0]) {
      error.value = data.errors.__all__[0];
    } else if (status === 400) {
      error.value = "Invalid username or password.";
    } else if (status === 403) {
      error.value = "Your account is not approved or is inactive.";
    } else {
      error.value = "Login failed. Please try again.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - var(--nav-h));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  background: linear-gradient(180deg, rgba(248, 249, 250, 0.6), rgba(255, 255, 255, 1));
}

.login-card {
  width: 100%;
  max-width: 520px;
  border-radius: 12px;
  background-color: #f8f9fa;
}
</style>
