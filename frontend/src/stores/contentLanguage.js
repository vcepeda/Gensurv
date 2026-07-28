import { defineStore } from "pinia";

// Shared language choice for bilingual content blocks on Home and About only
// - no other page reads this, so it has zero effect anywhere else (Help,
// Dashboard, uploads, etc. stay English-only regardless of this setting).
export const useContentLanguageStore = defineStore("contentLanguage", {
  state: () => ({
    lang: "en",
  }),

  actions: {
    setLang(lang) {
      this.lang = lang === "de" ? "de" : "en";
    },
  },
});
