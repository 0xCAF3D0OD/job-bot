import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import PlaceholderView from "./views/PlaceholderView.vue";
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
  {
    path: "/offres",
    name: "offers",
    label: "Offres",
    since: "0.4.0",
    description: "Offres collectées, filtrées et notées, à préparer, ignorer ou garder pour plus tard.",
  },
  {
    path: "/profil",
    name: "profile",
    label: "Profil",
    since: "0.3.0",
    description: "Tes documents et les blocs de profil sur lesquels l'IA s'appuie.",
  },
  {
    path: "/prerequis",
    name: "criteria",
    label: "Prérequis",
    since: "0.3.0",
    description: "Formulaire des prérequis non négociables : lieu, taux, contrats, langues, salaire.",
  },
  {
    path: "/journal",
    name: "journal",
    label: "Journal",
    since: "0.2.0",
    description: "Recherches exécutées (alertes reçues) et candidatures envoyées.",
  },
  {
    path: "/orp",
    name: "orp",
    label: "ORP",
    since: "0.6.0",
    description: "Export mensuel des preuves de recherches d'emploi.",
  },
  {
    path: "/reglages",
    name: "settings",
    label: "Réglages",
    since: "0.3.0",
    description: "Objectif mensuel ORP, seuil de notification, plafond du coût IA.",
  },
  { path: "/etat", name: "status", label: "État" },
];

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/etat" },
  ...navigation.map((entry): RouteRecordRaw =>
    entry.name === "status"
      ? { path: entry.path, name: entry.name, component: StatusView }
      : { path: entry.path, name: entry.name, component: PlaceholderView, props: { entry } },
  ),
  { path: "/:pathMatch(.*)*", redirect: "/etat" },
];

export const router = createRouter({ history: createWebHistory(), routes });
