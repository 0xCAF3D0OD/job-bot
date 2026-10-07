import type { Component } from "vue";
import { createRouter, createWebHistory, type LocationQuery, type RouteRecordRaw } from "vue-router";

import { useAuth } from "./composables/useAuth";
import ApplicationsView from "./views/ApplicationsView.vue";
import JobsView from "./views/JobsView.vue";
import LoginView from "./views/LoginView.vue";
import NewsView from "./views/NewsView.vue";
import OffersView from "./views/OffersView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";
import PreparationView from "./views/PreparationView.vue";
import ProfileView from "./views/ProfileView.vue";
import SettingsView from "./views/SettingsView.vue";
import TodayView from "./views/TodayView.vue";
import TrainingsView from "./views/TrainingsView.vue";

export interface NavEntry {
  path: string;
  name: string;
  label: string;
  // Version du cadrage (docs/01-cadrage.md §11) qui livre la page.
  since?: string;
  description?: string;
}

// Menu (docs/19 §1) : une entrée par question. Offres, suivi, preuves ORP et journal sont
// des onglets de la rubrique Candidatures ; l'État est une section des Réglages.
export const navigation: NavEntry[] = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui" },
  { path: "/candidatures", name: "jobs", label: "Candidatures" },
  { path: "/actualites", name: "news", label: "Actualités" },
  { path: "/formations", name: "trainings", label: "Formations" },
  { path: "/profil", name: "profile", label: "Profil" },
  { path: "/reglages", name: "settings", label: "Réglages" },
];

// Onglets de la rubrique Candidatures (docs/19 §2).
export type JobsTab = "offres" | "suivi" | "preuves" | "journal";

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, Component> = {
  news: NewsView,
  trainings: TrainingsView,
  profile: ProfileView,
  settings: SettingsView,
  today: TodayView,
};

function keepMonth(query: LocationQuery): Record<string, string> {
  return typeof query.mois === "string" ? { mois: query.mois } : {};
}

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/aujourdhui" },
  // Anciennes adresses : liens des alertes, des rappels ntfy, marque-pages.
  { path: "/prerequis", redirect: "/profil" },
  { path: "/offres", redirect: (to) => ({ path: "/candidatures/offres", query: to.query }) },
  {
    path: "/offres/:id(\\d+)/preparer",
    redirect: (to) => ({ path: `/candidatures/offres/${String(to.params.id)}/preparer` }),
  },
  { path: "/journal", redirect: "/candidatures/journal" },
  {
    path: "/orp",
    redirect: (to) => ({
      path: to.query.onglet === "journal" ? "/candidatures/journal" : "/candidatures/preuves",
      query: keepMonth(to.query),
    }),
  },
  { path: "/etat", redirect: { path: "/reglages", hash: "#etat" } },
  ...navigation
    .filter((entry) => entry.name !== "jobs")
    .map(
      (entry): RouteRecordRaw => ({
        path: entry.path,
        name: entry.name,
        component: views[entry.name] ?? PlaceholderView,
        props: views[entry.name] ? false : { entry },
      }),
    ),
  {
    path: "/candidatures",
    component: JobsView,
    children: [
      {
        // /candidatures seul : les Offres ; les anciens liens (?vue=orp, ?vue=journal, ?mois=…)
        // retrouvent leur onglet.
        path: "",
        redirect: (to) => {
          const query = keepMonth(to.query);
          if (to.query.vue === "orp") return { path: "/candidatures/preuves", query };
          if (to.query.vue === "journal") return { path: "/candidatures/journal" };
          if (query.mois) return { path: "/candidatures/suivi", query };
          return { path: "/candidatures/offres" };
        },
      },
      { path: "offres", name: "offers", component: OffersView, meta: { tab: "offres" } },
      { path: "suivi", name: "applications", component: ApplicationsView, props: { view: "suivi" }, meta: { tab: "suivi" } },
      { path: "preuves", name: "orp", component: ApplicationsView, props: { view: "orp" }, meta: { tab: "preuves" } },
      { path: "journal", name: "journal", component: ApplicationsView, props: { view: "journal" }, meta: { tab: "journal" } },
    ],
  },
  // Connexion (docs/18 §1).
  { path: "/connexion", name: "login", component: LoginView },
  // Hors onglets : on y arrive depuis une offre (« Préparer ma candidature »).
  { path: "/candidatures/offres/:id(\\d+)/preparer", name: "preparation", component: PreparationView },
  { path: "/:pathMatch(.*)*", redirect: "/aujourdhui" },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 80 } : { top: 0 }),
});

// Ouvert sans connexion : les Actualités et la page de connexion (docs/18 §1).
export const PUBLIC_ROUTES = new Set(["news", "login"]);

router.beforeEach(async (to) => {
  const { loggedIn, load } = useAuth();
  await load();
  if (to.name === "login") {
    if (!loggedIn.value) return true;
    const wanted = typeof to.query.suite === "string" ? to.query.suite : "";
    return wanted.startsWith("/") && !wanted.startsWith("//") ? wanted : "/aujourdhui";
  }
  if (loggedIn.value || PUBLIC_ROUTES.has(String(to.name))) return true;
  return { name: "login", query: { suite: to.fullPath } };
});
