import type { Component } from "vue";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import ApplicationsView from "./views/ApplicationsView.vue";
import CriteriaView from "./views/CriteriaView.vue";
import JournalView from "./views/JournalView.vue";
import OffersView from "./views/OffersView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";
import PreparationView from "./views/PreparationView.vue";
import ProfileView from "./views/ProfileView.vue";
import SettingsView from "./views/SettingsView.vue";
import StatusView from "./views/StatusView.vue";

export interface NavEntry {
  path: string;
  name: string;
  label: string;
  // Version du cadrage (docs/01-cadrage.md §11) qui livre la page.
  since?: string;
  description?: string;
}

// Menu définitif : les pages vides indiquent la version qui les remplira.
export const navigation: NavEntry[] = [
  { path: "/offres", name: "offers", label: "Offres" },
  { path: "/candidatures", name: "applications", label: "Candidatures" },
  { path: "/profil", name: "profile", label: "Profil" },
  { path: "/prerequis", name: "criteria", label: "Prérequis" },
  { path: "/journal", name: "journal", label: "Journal" },
  {
    path: "/orp",
    name: "orp",
    label: "ORP",
    since: "0.6.0",
    description: "Export mensuel des preuves de recherches d'emploi.",
  },
  { path: "/reglages", name: "settings", label: "Réglages" },
  { path: "/etat", name: "status", label: "État" },
];

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, Component> = {
  offers: OffersView,
  applications: ApplicationsView,
  profile: ProfileView,
  journal: JournalView,
  criteria: CriteriaView,
  settings: SettingsView,
  status: StatusView,
};

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/etat" },
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
  { path: "/:pathMatch(.*)*", redirect: "/etat" },
];

export const router = createRouter({ history: createWebHistory(), routes });
