import { defineStore } from "pinia";
import { me, logout as apiLogout } from "@/api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    isAuthenticated: false,
    username: null,
    isSuperuser: false,
    isStaff: false,
    isLoading: false,
  }),

  actions: {
    async fetchUser() {
      this.isLoading = true;
      try {
        const data = await me();
        this.isAuthenticated = !!data?.is_authenticated;
        this.username = data?.username ?? null;
        this.isSuperuser = !!data?.is_superuser;
        this.isStaff = !!data?.is_staff;
      } catch (e) {
        this.isAuthenticated = false;
        this.username = null;
        this.isSuperuser = false;
        this.isStaff = false;
      } finally {
        this.isLoading = false;
      }
    },

    async logout() {
      await apiLogout();
      this.isAuthenticated = false;
      this.username = null;
      this.isSuperuser = false;
      this.isStaff = false;
    }
  }
});