import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "./stores/auth";
import LoginView from "@/views/LoginView.vue";
import LogoutView from "@/views/LogoutView.vue";
import RegisterView from "./views/RegisterView.vue";
import PasswordResetView from "./views/PasswordReset.vue";
import HomeView from "./views/HomeView.vue";
import HelpView from "./views/HelpView.vue";
import FooterLinksView from "./views/FooterLinksView.vue";
import AboutView from "./views/AboutView.vue";
import ResearchView from "./views/ResearchView.vue";
import UploadView from "./views/UploadView.vue";
import tempDashboardView from "./views/tempDashboardView.vue";
import ResubmitView from "./views/ResubmitView.vue";
import SubmissionResultsView from "./views/SubmissionResultView.vue"
import MetadataStatisticsView from "./views/MetadataStatisticsView.vue"
import GlobalStatisticsView from "./views/GlobalStatisticsView.vue"

const routes = [
  { path: "/", component: HomeView },
  { path: "/login", name: "login", component: LoginView },
  { path: "/logout", component: LogoutView },
  { path: "/register", component: RegisterView },
  { path: "/password-reset", name: "password_reset", component: PasswordResetView },
  {
    path: "/password-reset/:uid/:token",
    name: "password_reset_confirm",
    component: PasswordResetView,
    props: true,
  },
  { path: "/help", component: HelpView },
  { path: "/impressum", component: FooterLinksView, meta: {pageKey: "impressum" }},
  { path: "/contact", component: FooterLinksView, meta: {pageKey: "contact" }},
  { path: "/privacy", component: FooterLinksView, meta: {pageKey: "privacy" }},
  { path: "/accessibility", component: FooterLinksView, meta: {pageKey: "accessibility" }},
  { path: "/about", component: AboutView },
  { path: "/research", component: ResearchView },
  { path: "/upload", component: UploadView },
  { path: "/dashboard", component: tempDashboardView },
  {
    path: "/statistics",
    name: "global_statistics",
    component: GlobalStatisticsView,
  },
  {
      path: "/submissions/:submissionId/results",
      name: "submission_results",
      component: SubmissionResultsView,
    },
  {
    path: "/submissions/:submissionId/statistics",
    name: "metadata_statistics",
    component: MetadataStatisticsView,
    meta: { requiresAuth: true }
  },
  { 
    path: "/resubmit/:submissionId/:fileType", 
    name: "resubmit",
    component: ResubmitView,
    meta: { requiresAuth: true }
  },

];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    // Always scroll to top on route change
    return { top: 0, left: 0 }
  },
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (!to.meta.requiresAuth) return true;

  if (auth.isAuthenticated) return true;

  await auth.fetchUser();

  if (!auth.isAuthenticated) {
    return { name: "login", query: { next: to.fullPath } };
  }

  return true;
});

export default router;
