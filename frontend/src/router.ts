import type { Component } from "vue";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import ApplicationsView from "./views/ApplicationsView.vue";
import OffersView from "./views/OffersView.vue";
import OrpView from "./views/OrpView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";
import PreparationView from "./views/PreparationView.vue";
import ProfileView from "./views/ProfileView.vue";
import SettingsView from "./views/SettingsView.vue";
import TodayView from "./views/TodayView.vue";

export interface NavEntry {
  path: string;
  name: string;
  label: string;
  // Version du cadrage (docs/01-cadrage.md §11) qui livre la page.
  since?: string;
  description?: string;
}

// Menu (docs/10 §2 c) : le Journal est un onglet de la page ORP, l'État une section des Réglages.
export const navigation: NavEntry[] = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui" },
  { path: "/offres", name: "offers", label: "Offres" },
  { path: "/candidatures", name: "applications", label: "Candidatures" },
  { path: "/orp", name: "orp", label: "ORP" },
  { path: "/profil", name: "profile", label: "Profil" },
  { path: "/reglages", name: "settings", label: "Réglages" },
];

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, Component> = {
  offers: OffersView,
  applications: ApplicationsView,
  orp: OrpView,
  profile: ProfileView,
  settings: SettingsView,
  today: TodayView,
};

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/aujourdhui" },
  // Anciennes adresses (avant 0.6.1).
  { path: "/prerequis", redirect: "/profil" },
  { path: "/journal", redirect: { path: "/orp", query: { onglet: "journal" } } },
  { path: "/etat", redirect: { path: "/reglages", hash: "#etat" } },
  ...navigation.map(
    (entry): RouteRecordRaw => ({
      path: entry.path,
      name: entry.name,
      component: views[entry.name] ?? PlaceholderView,
      props: views[entry.name] ? false : { entry },
    }),
  ),
  // Hors menu : on y arrive depuis une offre (« Préparer ma candidature »).
  { path: "/offres/:id(\\d+)/preparer", name: "preparation", component: PreparationView },
  { path: "/:pathMatch(.*)*", redirect: "/aujourdhui" },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 80 } : { top: 0 }),
});
