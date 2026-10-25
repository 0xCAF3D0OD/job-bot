import { createRouter, createWebHistory, type LocationQuery, type RouteRecordRaw } from "vue-router";

import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { startPage } from "./composables/usePageTransition";
import type { IconName } from "./icons";
import PlaceholderView from "./views/PlaceholderView.vue";

// Chaque page se charge quand on l'ouvre (docs/117 §3) : la connexion et Aujourd'hui ne
// téléchargent plus Préparer, le Bilan ou les Réglages.
const AlertsView = () => import("./views/AlertsView.vue");
const InsightsView = () => import("./views/InsightsView.vue");
const OrpMeetingView = () => import("./views/OrpMeetingView.vue");
const DiagnosticView = () => import("./views/DiagnosticView.vue");
const AccessView = () => import("./views/AccessView.vue");
const AccessibilityView = () => import("./views/AccessibilityView.vue");
const TermsView = () => import("./views/TermsView.vue");
const AboutView = () => import("./views/AboutView.vue");
const DiscoverView = () => import("./views/DiscoverView.vue");
const ExtensionLinkView = () => import("./views/ExtensionLinkView.vue");
const PrivacyView = () => import("./views/PrivacyView.vue");
const WelcomeView = () => import("./views/WelcomeView.vue");
const ApplicationsView = () => import("./views/ApplicationsView.vue");
const JobsView = () => import("./views/JobsView.vue");
const LoginView = () => import("./views/LoginView.vue");
const OffersView = () => import("./views/OffersView.vue");
const NotFoundView = () => import("./views/NotFoundView.vue");
const PreparationView = () => import("./views/PreparationView.vue");
const BilanView = () => import("./views/BilanView.vue");
const ProfileView = () => import("./views/ProfileView.vue");
const SettingsView = () => import("./views/SettingsView.vue");
const SignupView = () => import("./views/SignupView.vue");
const TodayView = () => import("./views/TodayView.vue");
const TrainingsView = () => import("./views/TrainingsView.vue");

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
  { path: "/bilan", name: "bilan", label: "Bilan", icon: "stats" },
  { path: "/profil", name: "profile", label: "Profil", icon: "user" },
  { path: "/reglages", name: "settings", label: "Réglages", icon: "settings" },
];
// Le menu principal : trois entrées, une question chacune (docs/126 §1) : Aujourd'hui (que
// faire ?), Candidatures (où en sont-elles ?), Bilan (qu'est-ce qui marche, quoi améliorer ?).
// Profil et Réglages s'ouvrent depuis le menu du compte.
export const mainMenu: NavEntry[] = navigation.filter((entry) => ["today", "jobs", "bilan"].includes(entry.name));

// Onglets de la rubrique Candidatures (docs/19 §2).
export type JobsTab = "offres" | "suivi" | "alertes" | "rendez-vous";
// Onglets du Bilan (docs/126 §1) : les résultats, puis ce qui aide à progresser.
export type BilanTab = "resultats" | "formations";

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, () => Promise<unknown>> = {
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
  // « Partager vers jobA1 » sur Android (manifeste, share_target) : le formulaire d'ajout.
  {
    path: "/ajouter-une-offre",
    redirect: (to) => ({ path: "/candidatures/offres", query: { ...to.query, ajouter: "1" } }),
  },
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
  // Formations est dans le Bilan (docs/126 §1) : les anciens liens y mènent, ceux de Progresser
  // (docs/90) compris. Les Actualités sont retirées (1.6.25) : leurs liens mènent au Bilan.
  { path: "/actualites", redirect: "/bilan" },
  { path: "/formations", redirect: (to) => ({ path: "/bilan/formations", query: to.query }) },
  { path: "/progresser", redirect: "/bilan" },
  { path: "/progresser/actualites", redirect: "/bilan" },
  { path: "/progresser/formations", redirect: (to) => ({ path: "/bilan/formations", query: to.query }) },
  ...navigation
    .filter((entry) => entry.name !== "jobs" && entry.name !== "bilan")
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
      // Le Bilan est une entrée du menu (docs/126 §1) : les anciens liens y mènent, avec le mois.
      { path: "bilan", redirect: (to) => ({ path: "/bilan", query: to.query }) },
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
    // Le Bilan (docs/42, docs/126 §1) : ce qui marche, puis Formations.
    path: "/bilan",
    component: BilanView,
    children: [
      { path: "", name: "insights", component: InsightsView, meta: { tab: "resultats" } },
      { path: "formations", name: "trainings", component: TrainingsView, meta: { tab: "formations" } },
      { path: "actualites", redirect: "/bilan" },
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
  // Accessibilité (docs/117 §1) : publique, liée depuis Données personnelles.
  { path: "/accessibilite", name: "accessibility", component: AccessibilityView },
  // Conditions d'utilisation (docs/125 §7) : publiques.
  { path: "/conditions", name: "terms", component: TermsView },
  // À propos (docs/126 §4) : publique.
  { path: "/a-propos", name: "about", component: AboutView },
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
export const PUBLIC_ROUTES = new Set(["discover", "login", "access", "signup", "privacy", "accessibility", "terms", "about"]);

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
// Le titre de l'onglet du navigateur, « Page · jobA1 » (WCAG 2.4.2, audit du 22.10.2026).
export const PAGE_TITLES: Record<string, string> = {
  today: "Aujourd'hui",
  offers: "Offres",
  applications: "Suivi",
  alerts: "Alertes",
  insights: "Bilan",
  "orp-meeting": "Rendez-vous ORP",
  preparation: "Préparer",
  trainings: "Formations",
  profile: "Profil",
  settings: "Réglages",
  diagnostic: "Diagnostic",
  login: "Connexion",
  access: "Accès",
  signup: "Demander un compte",
  discover: "La plateforme",
  privacy: "Données personnelles",
  accessibility: "Accessibilité",
  terms: "Conditions d'utilisation",
  about: "À propos",
  welcome: "Bienvenue",
  "extension-link": "Extension",
  "not-found": "Page introuvable",
};

export function pageTitle(name: unknown): string {
  const page = typeof name === "string" ? PAGE_TITLES[name] : undefined;
  return page ? `${page} · jobA1` : "jobA1";
}

router.afterEach((to, from) => {
  document.title = pageTitle(to.name);
  useJobsMemory().remember(to.fullPath);
  if (to.name !== from.name) startPage(typeof to.name === "string" ? to.name : null);
});
