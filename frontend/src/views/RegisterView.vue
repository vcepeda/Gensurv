<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">Register</h1>

      <div v-if="serverMessage" class="alert alert-info" role="alert">
        {{ serverMessage }}
      </div>

      <div v-if="generalError" class="alert alert-danger" role="alert">
        {{ generalError }}
      </div>

      <!-- Form disappears after successful registration -->
      <form v-if="!registrationComplete" @submit.prevent="onSubmit" novalidate>
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input
            v-model.trim="form.username"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('username') }"
            autocomplete="username"
            required
          />
          <div v-if="hasFieldError('username')" class="invalid-feedback">
            {{ firstFieldError('username') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Name</label>
          <input
            v-model.trim="form.name"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('name') }"
            autocomplete="name"
            required
          />
          <div v-if="hasFieldError('name')" class="invalid-feedback">
            {{ firstFieldError('name') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Email</label>
          <input
            v-model.trim="form.email"
            type="email"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('email') }"
            autocomplete="email"
            required
          />
          <div v-if="hasFieldError('email')" class="invalid-feedback">
            {{ firstFieldError('email') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Institution</label>
          <input
            v-model.trim="form.institution"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('institution') }"
            autocomplete="organization"
            required
          />
          <div v-if="hasFieldError('institution')" class="invalid-feedback">
            {{ firstFieldError('institution') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Password</label>
          <input
            v-model="form.password1"
            type="password"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('password1') }"
            autocomplete="new-password"
            required
          />
          <div v-if="hasFieldError('password1')" class="invalid-feedback">
            {{ firstFieldError('password1') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Confirm Password</label>
          <input
            v-model="form.password2"
            type="password"
            class="form-control"
            :class="{ 'is-invalid': hasFieldError('password2') }"
            autocomplete="new-password"
            required
          />
          <div v-if="hasFieldError('password2')" class="invalid-feedback">
            {{ firstFieldError('password2') }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Message</label>
          <textarea
            v-model.trim="form.message"
            class="form-control"
            rows="4"
            :class="{ 'is-invalid': hasFieldError('message') }"
            required
          ></textarea>
          <div v-if="hasFieldError('message')" class="invalid-feedback">
            {{ firstFieldError('message') }}
          </div>
        </div>

        <button class="btn btn-primary w-100" type="submit" :disabled="submitting">
          <span
            v-if="submitting"
            class="spinner-border spinner-border-sm me-2"
            aria-hidden="true"
          ></span>
          Register
        </button>

        <p class="mt-3 mb-0 text-center">
          Already have an account?
          <RouterLink to="/login">Login</RouterLink>
        </p>
      </form>

      <!-- Optional: after completion, show a single CTA -->
      <div v-else class="text-center mt-3">
        <RouterLink to="/login" class="btn btn-outline-primary">
          Back to Login
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import apiClient from "@/api/client";

const submitting = ref(false);
const serverMessage = ref("");
const generalError = ref("");
const fieldErrors = ref({});
const registrationComplete = ref(false);

const form = reactive({
  username: "",
  name: "",
  email: "",
  institution: "",
  password1: "",
  password2: "",
  message: "",
});

function hasFieldError(field) {
  return Array.isArray(fieldErrors.value?.[field]) && fieldErrors.value[field].length > 0;
}

function firstFieldError(field) {
  return hasFieldError(field) ? fieldErrors.value[field][0] : "";
}

function resetErrors() {
  serverMessage.value = "";
  generalError.value = "";
  fieldErrors.value = {};
}

async function onSubmit() {
  submitting.value = true;
  resetErrors();

  try {
    // Ensure CSRF cookie exists (safe even if already set)
    await apiClient.get("/api/csrf/");

    // Use relative URL (baseURL is "/")
    const res = await apiClient.post("/api/register/", {
      username: form.username,
      name: form.name,
      email: form.email,
      institution: form.institution,
      password1: form.password1,
      password2: form.password2,
      message: form.message,
    });

    if (res?.data?.status === "pending") {
      serverMessage.value =
        "Your registration is pending admin approval. Please check your email for updates.";
      registrationComplete.value = true;
    } else {
      serverMessage.value = "Registration submitted.";
      registrationComplete.value = true;
    }
  } catch (err) {
    const status = err?.response?.status;
    const data = err?.response?.data;

    if (status === 400 && data && typeof data === "object") {
      if (data.detail) {
        generalError.value = data.detail;
      } else if (data.errors) {
        fieldErrors.value = data.errors;
        generalError.value = data.errors?.__all__?.[0] || "";
      } else {
        fieldErrors.value = data;
        generalError.value = data?.__all__?.[0] || "";
      }
    } else if (status === 403) {
      generalError.value = data?.detail || "You are not allowed to perform this action.";
    } else {
      generalError.value = "Registration failed. Please try again.";
    }
  } finally {
    submitting.value = false;
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
  background: #f5f6f7;
  border: 1px solid #e0e3e7;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}

.auth-title {
  margin-bottom: 1.25rem;
}
</style>
