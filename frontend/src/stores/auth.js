import { defineStore } from "pinia";
import { me, logout as apiLogout } from "@/api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    isAuthenticated: false,
    username: null,
    isLoading: false,
  }),

  actions: {
    async fetchUser() {
      this.isLoading = true;
      try {
        const data = await me();
        this.isAuthenticated = !!data?.is_authenticated;
        this.username = data?.username ?? null;
      } catch (e) {
        this.isAuthenticated = false;
        this.username = null;
      } finally {
        this.isLoading = false;
      }
    },

    async logout() {
      await apiLogout();
      this.isAuthenticated = false;
      this.username = null;
    }
  }
});
