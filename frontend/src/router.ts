import type { Component } from "vue";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import CriteriaView from "./views/CriteriaView.vue";
import JournalView from "./views/JournalView.vue";
import OffersView from "./views/OffersView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";
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
  {
    path: "/profil",
    name: "profile",
    label: "Profil",
    since: "0.3.0",
    description: "Tes documents et les blocs de profil sur lesquels l'IA s'appuie.",
  },
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
  { path: "/:pathMatch(.*)*", redirect: "/etat" },
];

export const router = createRouter({ history: createWebHistory(), routes });
