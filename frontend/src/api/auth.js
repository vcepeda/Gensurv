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
