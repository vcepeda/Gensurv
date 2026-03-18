// src/api/auth.js
import apiClient from "./client";

export async function login(username, password) {
  // make sure cookie exists
  await apiClient.get("/api/csrf/");

  const res = await apiClient.post("/api/login/", { username, password });
  return res.data;
}

export async function logout() {
  await apiClient.post("/api/logout/");
}

export async function me() {
  const res = await apiClient.get("/api/me/");
  return res.data;
}

export async function requestPasswordReset(email) {
  await apiClient.get("/api/csrf/");
  const res = await apiClient.post("/api/password-reset/", { email });
  return res.data;
}

export async function confirmPasswordReset(uid, token, newPassword1, newPassword2) {
  await apiClient.get("/api/csrf/");
  const res = await apiClient.post("/api/password-reset/confirm/", {
    uid,
    token,
    new_password1: newPassword1,
    new_password2: newPassword2,
  });
  return res.data;
}
