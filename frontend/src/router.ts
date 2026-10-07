import type { Component } from "vue";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useAuth } from "./composables/useAuth";
import ApplicationsView from "./views/ApplicationsView.vue";
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
  // Dans le menu du compte (icône en haut à droite) plutôt que dans la barre.
  account?: boolean;
}

// Menu (docs/10 §2 c, docs/18 §2) : preuves ORP et journal sont des onglets de la page
// Candidatures, l'État une section des Réglages.
export const navigation: NavEntry[] = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui" },
  { path: "/offres", name: "offers", label: "Offres" },
  { path: "/candidatures", name: "applications", label: "Candidatures" },
  { path: "/actualites", name: "news", label: "Actualités" },
  { path: "/formations", name: "trainings", label: "Formations" },
  { path: "/profil", name: "profile", label: "Profil", account: true },
  { path: "/reglages", name: "settings", label: "Réglages", account: true },
];

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, Component> = {
  offers: OffersView,
  applications: ApplicationsView,
  news: NewsView,
  trainings: TrainingsView,
  profile: ProfileView,
  settings: SettingsView,
  today: TodayView,
};

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/aujourdhui" },
  // Anciennes adresses (avant 0.6.1).
  { path: "/prerequis", redirect: "/profil" },
  { path: "/journal", redirect: { path: "/candidatures", query: { vue: "journal" } } },
  // Page ORP réunie aux Candidatures (0.11) : les liens des alertes et des rappels y mènent.
  {
    path: "/orp",
    redirect: (to) => ({
      path: "/candidatures",
      query: {
        vue: to.query.onglet === "journal" ? "journal" : "orp",
        ...(typeof to.query.mois === "string" ? { mois: to.query.mois } : {}),
      },
    }),
  },
  { path: "/etat", redirect: { path: "/reglages", hash: "#etat" } },
  ...navigation.map(
    (entry): RouteRecordRaw => ({
      path: entry.path,
      name: entry.name,
      component: views[entry.name] ?? PlaceholderView,
      props: views[entry.name] ? false : { entry },
    }),
  ),
  // Connexion (docs/18 §1).
  { path: "/connexion", name: "login", component: LoginView },
  // Hors menu : on y arrive depuis une offre (« Préparer ma candidature »).
  { path: "/offres/:id(\\d+)/preparer", name: "preparation", component: PreparationView },
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
