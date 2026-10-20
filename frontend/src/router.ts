import type { Component } from "vue";
import { createRouter, createWebHistory, type LocationQuery, type RouteRecordRaw } from "vue-router";

import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { useProgressMemory } from "./composables/useProgressMemory";
import { startPage } from "./composables/usePageTransition";
import AlertsView from "./views/AlertsView.vue";
import InsightsView from "./views/InsightsView.vue";
import OrpMeetingView from "./views/OrpMeetingView.vue";
import DiagnosticView from "./views/DiagnosticView.vue";
import AccessView from "./views/AccessView.vue";
import DiscoverView from "./views/DiscoverView.vue";
import ExtensionLinkView from "./views/ExtensionLinkView.vue";
import PrivacyView from "./views/PrivacyView.vue";
import WelcomeView from "./views/WelcomeView.vue";
import ApplicationsView from "./views/ApplicationsView.vue";
import JobsView from "./views/JobsView.vue";
import LoginView from "./views/LoginView.vue";
import NewsView from "./views/NewsView.vue";
import OffersView from "./views/OffersView.vue";
import NotFoundView from "./views/NotFoundView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";
import PreparationView from "./views/PreparationView.vue";
import ProgressView from "./views/ProgressView.vue";
import ProfileView from "./views/ProfileView.vue";
import SettingsView from "./views/SettingsView.vue";
import SignupView from "./views/SignupView.vue";
import TodayView from "./views/TodayView.vue";
import TrainingsView from "./views/TrainingsView.vue";
import type { IconName } from "./icons";

export interface NavEntry {
  path: string;
  name: string;
  label: string;
  // L'icône devant le nom dans le menu (docs/101).
  icon?: IconName;
  // Version du cadrage (docs/01-cadrage.md §11) qui livre la page.
  since?: string;
  description?: string;
}

// Menu (docs/19 §1) : une entrée par question. Offres, suivi, preuves ORP et alertes sont
// des onglets de la rubrique Candidatures ; l'État est une section des Réglages.
export const navigation: NavEntry[] = [
  { path: "/aujourdhui", name: "today", label: "Aujourd'hui", icon: "calendar" },
  { path: "/candidatures", name: "jobs", label: "Candidatures", icon: "check-circle" },
  { path: "/progresser", name: "progress", label: "Progresser", icon: "book" },
  { path: "/profil", name: "profile", label: "Profil", icon: "user" },
  { path: "/reglages", name: "settings", label: "Réglages", icon: "settings" },
];
// Le menu principal : les deux pages de travail (docs/89, docs/90, docs/92). Progresser
// s'ouvre depuis l'étincelle de la capsule, Profil et Réglages depuis le menu du compte ; ils
// gardent leur adresse et leur titre.
export const mainMenu: NavEntry[] = navigation.filter((entry) => ["today", "jobs"].includes(entry.name));

// Onglets de la rubrique Candidatures (docs/19 §2).
export type JobsTab = "offres" | "suivi" | "alertes" | "bilan" | "rendez-vous";
// Onglets de Progresser (docs/90).
export type ProgressTab = "actualites" | "formations";

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, Component> = {
  profile: ProfileView,
  settings: SettingsView,
  today: TodayView,
};

function keepMonth(query: LocationQuery): Record<string, string> {
  return typeof query.mois === "string" ? { mois: query.mois } : {};
}

export const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/aujourdhui" },
  // Anciennes adresses : liens des alertes, des rappels ntfy, marque-pages.
  { path: "/prerequis", redirect: "/profil" },
  { path: "/offres", redirect: (to) => ({ path: "/candidatures/offres", query: to.query }) },
  {
    path: "/offres/:id(\\d+)/preparer",
    redirect: (to) => ({ path: `/candidatures/offres/${String(to.params.id)}/preparer` }),
  },
  { path: "/journal", redirect: "/candidatures/alertes" },
  {
    path: "/orp",
    redirect: (to) => ({
      path: to.query.onglet === "journal" ? "/candidatures/alertes" : "/candidatures/suivi",
      query: keepMonth(to.query),
    }),
  },
  { path: "/etat", redirect: "/reglages/diagnostic" },
  // Actualités et Formations sont dans Progresser (docs/90) : les anciens liens y mènent.
  { path: "/actualites", redirect: (to) => ({ path: "/progresser/actualites", query: to.query }) },
  { path: "/formations", redirect: (to) => ({ path: "/progresser/formations", query: to.query }) },
  ...navigation
    .filter((entry) => entry.name !== "jobs" && entry.name !== "progress")
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
          if (to.query.vue === "orp") return { path: "/candidatures/suivi", query };
          if (to.query.vue === "journal") return { path: "/candidatures/alertes" };
          if (query.mois) return { path: "/candidatures/suivi", query };
          return { path: "/candidatures/offres" };
        },
      },
      { path: "offres", name: "offers", component: OffersView, meta: { tab: "offres" } },
      { path: "suivi", name: "applications", component: ApplicationsView, meta: { tab: "suivi" } },
      // Preuves ORP fondues dans le Suivi (docs/22 §1) : les anciens liens y mènent, avec le mois.
      { path: "preuves", redirect: (to) => ({ path: "/candidatures/suivi", query: to.query }) },
      // Mes alertes et alertes reçues (docs/20 §1) ; l'ancien « Journal des recherches ».
      { path: "alertes", name: "alerts", component: AlertsView, meta: { tab: "alertes" } },
      { path: "journal", redirect: "/candidatures/alertes" },
      // Ce qui marche dans ta recherche (docs/42).
      { path: "bilan", name: "insights", component: InsightsView, meta: { tab: "bilan" } },
      // Le rendez-vous avec le conseiller ORP (docs/83).
      {
        path: "rendez-vous-orp",
        name: "orp-meeting",
        component: OrpMeetingView,
        meta: { tab: "rendez-vous" },
      },
    ],
  },
  {
    path: "/progresser",
    component: ProgressView,
    children: [
      // /progresser seul : le dernier onglet choisi, sinon les Actualités.
      { path: "", redirect: () => useProgressMemory().last.value },
      { path: "actualites", name: "news", component: NewsView, meta: { tab: "actualites" } },
      { path: "formations", name: "trainings", component: TrainingsView, meta: { tab: "formations" } },
    ],
  },
  // Diagnostic technique, sorti des Réglages (docs/21 §6).
  { path: "/reglages/diagnostic", name: "diagnostic", component: DiagnosticView },
  // Connexion (docs/18 §1).
  { path: "/connexion", name: "login", component: LoginView },
  // Lien d'invitation ou de réinitialisation, transmis par l'exploitant (docs/65 §2).
  { path: "/acces/:token", name: "access", component: AccessView },
  // Demander un compte, validé ensuite par l'exploitant (docs/102).
  { path: "/inscription", name: "signup", component: SignupView },
  // La plateforme présentée à qui n'est pas connecté (docs/67, complément).
  { path: "/la-plateforme", name: "discover", component: DiscoverView },
  // Ce que la plateforme garde, lisible sans connexion (docs/65 §6).
  { path: "/tes-donnees", name: "privacy", component: PrivacyView },
  // L'accueil après la première connexion (docs/66), plein écran, sans menu.
  { path: "/bienvenue", name: "welcome", component: WelcomeView, meta: { bare: true } },
  // Relier l'extension du navigateur en un clic, ouverte par l'extension (docs/71 §4).
  { path: "/extension/relier", name: "extension-link", component: ExtensionLinkView },
  // Hors onglets : on y arrive depuis une offre (« Préparer ma candidature »).
  { path: "/candidatures/offres/:id(\\d+)/preparer", name: "preparation", component: PreparationView },
  // Adresse inconnue (docs/59 §5) : une page qui le dit.
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 80 } : { top: 0 }),
});

// Ouvert sans connexion : la présentation de la plateforme, la connexion (docs/18 §1), les liens
// d'accès, la demande de compte (docs/102) et ce qui est gardé. Les Actualités demandent la
// connexion depuis la 0.55.0 (docs/67).
export const PUBLIC_ROUTES = new Set(["discover", "login", "access", "signup", "privacy"]);

router.beforeEach(async (to) => {
  const { loggedIn, load } = useAuth();
  await load();
  // Connecté, la connexion et la demande de compte renvoient vers l'application.
  if (to.name === "login" || to.name === "signup") {
    if (!loggedIn.value) return true;
    const wanted = typeof to.query.suite === "string" ? to.query.suite : "";
    return wanted.startsWith("/") && !wanted.startsWith("//") ? wanted : "/aujourdhui";
  }
  // Un nouveau compte passe d'abord par l'accueil (docs/66 §4) ; « Plus tard » le laisse aller.
  const { me } = useAuth();
  if (loggedIn.value && me.value?.welcome === "pending" && to.name !== "welcome" && !PUBLIC_ROUTES.has(String(to.name))) {
    return { name: "welcome" };
  }
  // Le Diagnostic technique, à l'exploitant seulement (docs/108 §3) : un invité revient aux Réglages.
  if (to.name === "diagnostic" && loggedIn.value && me.value?.auth_enabled && !me.value.is_owner) {
    return { path: "/reglages" };
  }
  if (loggedIn.value || PUBLIC_ROUTES.has(String(to.name))) return true;
  return { name: "login", query: { suite: to.fullPath } };
});

// Retour à la dernière page de la rubrique Candidatures depuis le menu (docs/19). À l'arrivée
// sur une autre page, sa transition si elle charge des données (docs/61 §2) ; pas en changeant
// seulement un filtre, un mois ou un onglet dans la page.
router.afterEach((to, from) => {
  useJobsMemory().remember(to.fullPath);
  useProgressMemory().remember(to.fullPath);
  if (to.name !== from.name) startPage(typeof to.name === "string" ? to.name : null);
});
