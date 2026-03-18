<template>
  <div class="auth-page">
    <div class="auth-card card shadow-sm">
      <div class="card-body p-4">
        <h2 class="text-center mb-3">{{ isConfirmMode ? "Set New Password" : "Reset Password" }}</h2>

        <div v-if="successMessage" class="alert alert-success" role="alert">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="alert alert-danger" role="alert">
          {{ errorMessage }}
        </div>

        <form v-if="!done" @submit.prevent="onSubmit" novalidate>
          <div v-if="!isConfirmMode" class="mb-3">
            <label class="form-label">Email</label>
            <input
              v-model.trim="email"
              type="email"
              class="form-control"
              autocomplete="email"
              :disabled="loading"
              required
            />
          </div>

          <template v-else>
            <div class="mb-3">
              <label class="form-label">New Password</label>
              <input
                v-model="newPassword1"
                type="password"
                class="form-control"
                autocomplete="new-password"
                :disabled="loading"
                required
              />
            </div>

            <div class="mb-3">
              <label class="form-label">Confirm New Password</label>
              <input
                v-model="newPassword2"
                type="password"
                class="form-control"
                autocomplete="new-password"
                :disabled="loading"
                required
              />
            </div>
          </template>

          <div class="d-grid">
            <button class="btn btn-primary" type="submit" :disabled="loading">
              <span
                v-if="loading"
                class="spinner-border spinner-border-sm me-2"
                aria-hidden="true"
              ></span>
              {{ isConfirmMode ? "Update Password" : "Send Reset Link" }}
            </button>
          </div>
        </form>

        <div class="text-center mt-3">
          <RouterLink to="/login">Back to login</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { confirmPasswordReset, requestPasswordReset } from "@/api/auth";

const route = useRoute();

const loading = ref(false);
const done = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const email = ref("");
const newPassword1 = ref("");
const newPassword2 = ref("");

const uid = computed(() => route.params.uid || "");
const token = computed(() => route.params.token || "");
const isConfirmMode = computed(() => Boolean(uid.value && token.value));

function normalizeErrors(data) {
  if (!data || typeof data !== "object") return "Please try again.";

  if (data.detail) return data.detail;
  if (data.errors?.new_password1?.[0]) return data.errors.new_password1[0];
  if (data.errors?.new_password2?.[0]) return data.errors.new_password2[0];
  if (data.errors?.email?.[0]) return data.errors.email[0];
  return "Please check the form and try again.";
}

async function onSubmit() {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    if (!isConfirmMode.value) {
      await requestPasswordReset(email.value);
      done.value = true;
      successMessage.value =
        "If an account with that email exists, a reset link has been sent.";
      return;
    }

    await confirmPasswordReset(uid.value, token.value, newPassword1.value, newPassword2.value);
    done.value = true;
    successMessage.value = "Password updated successfully. You can now log in.";
  } catch (err) {
    errorMessage.value = normalizeErrors(err?.response?.data);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - var(--nav-h));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.auth-card {
  width: 100%;
  max-width: 520px;
  border-radius: 12px;
  background-color: #f8f9fa;
}
</style>
