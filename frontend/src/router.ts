import {
  createRouter,
  createWebHistory,
  type LocationQuery,
  type RouteLocationNormalized,
  type RouteLocationRaw,
  type RouteRecordRaw,
} from "vue-router";

import { useAssistant } from "./composables/useAssistant";
import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { startPage } from "./composables/usePageTransition";
import { PHONE_QUERY } from "./composables/usePhone";
import type { IconName } from "./icons";
import PlaceholderView from "./views/PlaceholderView.vue";

// Chaque page se charge quand on l'ouvre (docs/117 §3) : la connexion et Aujourd'hui ne
// téléchargent plus Préparer, le Bilan ou les Réglages.
const AlertsView = () => import("./views/AlertsView.vue");
const InsightsView = () => import("./views/InsightsView.vue");
const BilanOrpView = () => import("./views/BilanOrpView.vue");
const OrpMeetingView = () => import("./views/OrpMeetingView.vue");
const DiagnosticView = () => import("./views/DiagnosticView.vue");
const AccessView = () => import("./views/AccessView.vue");
const AccessibilityView = () => import("./views/AccessibilityView.vue");
const TermsView = () => import("./views/TermsView.vue");
const AboutView = () => import("./views/AboutView.vue");
const DiscoverView = () => import("./views/DiscoverView.vue");
const ExtensionLinkView = () => import("./views/ExtensionLinkView.vue");
const GetemallAuthorizeView = () => import("./views/GetemallAuthorizeView.vue");
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
const AccountView = () => import("./views/AccountView.vue");
const SettingsView = () => import("./views/SettingsView.vue");
const SignupView = () => import("./views/SignupView.vue");
const TodayView = () => import("./views/TodayView.vue");
const TriageView = () => import("./views/TriageView.vue");
const FollowUpsView = () => import("./views/FollowUpsView.vue");
const TrainingsView = () => import("./views/TrainingsView.vue");
const NotificationsView = () => import("./views/NotificationsView.vue");

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
  // La page Compte (docs/139 étape 10a) : le sommaire du profil et des réglages, l'onglet Compte du téléphone.
  { path: "/compte", name: "account", label: "Compte", icon: "user" },
  { path: "/profil", name: "profile", label: "Profil", icon: "user" },
  { path: "/reglages", name: "settings", label: "Réglages", icon: "settings" },
];
// Le menu principal : trois entrées, une question chacune (docs/126 §1) : Aujourd'hui (que
// faire ?), Candidatures (où en sont-elles ?), Bilan (qu'est-ce qui marche, quoi améliorer ?).
// Profil et Réglages s'ouvrent depuis la page Compte (décision de Kevin du 2026-11-05, C2).
export const mainMenu: NavEntry[] = navigation.filter((entry) => ["today", "jobs", "bilan"].includes(entry.name));

// Onglets de la rubrique Candidatures (docs/19 §2).
export type JobsTab = "offres" | "suivi" | "alertes" | "rendez-vous";
// Onglets du Bilan (docs/126 §1 ; docs/139 étape 8, B1) : l'ORP, les résultats, puis ce qui aide à progresser.
export type BilanTab = "orp" | "resultats" | "formations";

// Pages livrées ; les autres entrées du menu affichent la version qui les remplira.
const views: Record<string, () => Promise<unknown>> = {
  account: AccountView,
  profile: ProfileView,
  settings: SettingsView,
  today: TodayView,
};

function keepMonth(query: LocationQuery): Record<string, string> {
  return typeof query.mois === "string" ? { mois: query.mois } : {};
}

// Les Réglages n'ont plus de liste (décision de Kevin du 2026-11-05, C10) : sans rubrique, la page Compte. Les
// anciens liens gardent leur rubrique : « #agenda » (docs/48 §5), et l'ancienne rubrique Compte, qui menait à
// l'export et à la fermeture, devient Mes données.
const OLD_ANCHORS: Record<string, string> = {
  recherche: "recherche",
  notifications: "notifications",
  ia: "ia",
  profils: "plateforme",
  connexion: "donnees",
  agenda: "outils",
  extension: "connexions",
};
function settingsEntry(to: RouteLocationNormalized): RouteLocationRaw | true {
  // L'ancienne rubrique Compte (liens de l'assistant, retours de paiement) : la formule, ou Mes données
  // quand le lien venait fermer le compte.
  if (to.query.rubrique === "compte") {
    return { path: "/reglages", query: { ...to.query, rubrique: to.query.fermer ? "donnees" : "formule" } };
  }
  if (to.query.rubrique) return true;
  const anchor = OLD_ANCHORS[to.hash.slice(1)];
  if (anchor) return { path: "/reglages", query: { rubrique: anchor } };
  // L'ancien lien de l'état technique (docs/21 §6).
  if (to.hash === "#etat") return { path: "/reglages/diagnostic" };
  return { path: "/compte" };
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
      path: to.query.onglet === "journal" ? "/candidatures/alertes" : "/bilan/orp",
      query: keepMonth(to.query),
    }),
  },
  { path: "/etat", redirect: "/reglages/diagnostic" },
  // L'écran de tri des offres du jour (1.6.50) : un deuxième niveau d'Aujourd'hui.
  { path: "/aujourdhui/tri", name: "triage", component: TriageView },
  // Les relances une à une (planche « Tri et panneau de commande ») : un deuxième niveau du Suivi.
  { path: "/candidatures/relances", name: "follow-ups", component: FollowUpsView },
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
          if (to.query.vue === "orp") return { path: "/bilan/orp", query };
          if (to.query.vue === "journal") return { path: "/candidatures/alertes" };
          if (query.mois) return { path: "/bilan/orp", query };
          return { path: "/candidatures/offres" };
        },
      },
      // L'offre ouverte sur téléphone est une sous-page (docs/139 étape 6, O1) : /candidatures/offres/12, avec les
      // filtres de la liste. Même entrée que la liste : la vue reste montée, son défilement et ses filtres aussi.
      { path: "offres/:id(\\d+)?", name: "offers", component: OffersView, meta: { tab: "offres" } },
      // Envoyées. Un lien vers un mois ou un jour (rappels, assistant, Aujourd'hui) mène au Suivi ORP (B9,
      // 2026-11-04) ; celui d'une candidature (?candidature=) ou d'une recherche (?q=) reste ici.
      {
        path: "suivi",
        name: "applications",
        component: ApplicationsView,
        meta: { tab: "suivi" },
        beforeEnter: (to) =>
          (to.query.mois || to.query.jour) && !to.query.candidature && !to.query.q ? { path: "/bilan/orp", query: to.query } : true,
      },
      // Preuves ORP fondues dans le Suivi ORP (docs/22 §1, B9) : les anciens liens y mènent, avec le mois.
      { path: "preuves", redirect: (to) => ({ path: "/bilan/orp", query: to.query }) },
      // Mes alertes et alertes reçues (docs/20 §1) ; l'ancien « Journal des recherches ».
      { path: "alertes", name: "alerts", component: AlertsView, meta: { tab: "alertes" } },
      { path: "journal", redirect: "/candidatures/alertes" },
      // Le Bilan est une entrée du menu (docs/126 §1) : les anciens liens y mènent, avec le mois.
      { path: "bilan", redirect: (to) => ({ path: "/bilan/resultats", query: to.query }) },
      // Le rendez-vous avec le conseiller ORP (docs/83).
      {
        path: "rendez-vous-orp",
        name: "orp-meeting",
        component: OrpMeetingView,
        meta: { tab: "rendez-vous" },
      },
    ],
  },
  // Le Suivi ORP du mois (docs/139 étape 8b, maquette Orp) : une sous-page de Bilan › ORP.
  { path: "/bilan/orp", name: "orp-month", component: ApplicationsView },
  // « Pour l'ORP », une candidature à déclarer (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3) : plein écran.
  { path: "/bilan/orp/candidature/:id", name: "orp-fiche", component: () => import("./views/OrpFicheView.vue"), meta: { bare: true } },
  {
    // Le Bilan (docs/42, docs/126 §1) : ce qui marche, puis Formations.
    path: "/bilan",
    component: BilanView,
    children: [
      // L'ORP d'abord (maquette Explorer, B1, 2026-11-04) ; un ancien lien vers un mois (/bilan?mois=…) mène
      // aux Résultats de ce mois.
      {
        path: "",
        name: "bilan-orp",
        component: BilanOrpView,
        meta: { tab: "orp" },
        beforeEnter: (to) => (typeof to.query.mois === "string" ? { path: "/bilan/resultats", query: to.query } : true),
      },
      { path: "resultats", name: "insights", component: InsightsView, meta: { tab: "resultats" } },
      { path: "formations", name: "trainings", component: TrainingsView, meta: { tab: "formations" } },
      { path: "actualites", redirect: "/bilan" },
    ],
  },
  // Les notifications (maquette Notifications, docs/139 étape 9a) : la page de la cloche sur téléphone, « Tout
  // voir » sur ordinateur.
  { path: "/notifications", name: "notifications", component: NotificationsView },
  // Diagnostic technique, sorti des Réglages (docs/21 §6).
  { path: "/reglages/diagnostic", name: "diagnostic", component: DiagnosticView },
  // Connexion (docs/18 §1) : plein écran, son propre logo (maquette Connexion, 2026-11-05).
  { path: "/connexion", name: "login", component: LoginView, meta: { bare: true } },
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
  // L'Assistant, une page sur téléphone (docs/139 Q4, étape 11a) : le panneau, sur toute la page, au-dessus de la
  // barre du bas. Sur ordinateur, l'adresse ouvre le panneau sur l'Accueil.
  { path: "/assistant", name: "assistant", component: { render: () => null } },
  // Relier l'extension du navigateur en un clic, ouverte par l'extension (docs/71 §4).
  { path: "/extension/relier", name: "extension-link", component: ExtensionLinkView },
  // « Relier Get'emAll à ton compte ? » (docs/140, maquette AutoriserGetemall) : ouverte par Get'emAll, plein écran.
  { path: "/connexion/getemall", name: "getemall-authorize", component: GetemallAuthorizeView, meta: { bare: true } },
  // Hors onglets : on y arrive depuis une offre (« Préparer ma candidature »).
  { path: "/candidatures/offres/:id(\\d+)/preparer", name: "preparation", component: PreparationView },
  // Adresse inconnue (docs/59 §5) : une page qui le dit.
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView, meta: { bare: true } },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to, from) => {
    if (to.hash) return { el: to.hash, top: 80 };
    // Ouvrir ou fermer la sous-page d'une offre (téléphone, étape 6, O1) : la liste dessous garde son défilement.
    if (to.name === "offers" && from.name === "offers" && to.params.id !== from.params.id) return false;
    return { top: 0 };
  },
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
  if (loggedIn.value && me.value?.welcome === "pending" && to.name !== "welcome" && to.name !== "getemall-authorize" && !PUBLIC_ROUTES.has(String(to.name))) {
    return { name: "welcome" };
  }
  // L'Assistant : sa présence est connue avant le premier rendu de la barre du bas (AS8).
  if (loggedIn.value) {
    const assistant = useAssistant();
    await assistant.check();
    if (to.name === "assistant") {
      if (!assistant.available.value) return { path: "/aujourdhui" };
      if (!globalThis.matchMedia?.(PHONE_QUERY).matches) {
        assistant.open.value = true;
        return { path: "/aujourdhui" };
      }
    }
  }
  // Le Diagnostic technique, à l'exploitant seulement (docs/108 §3) : un invité revient au compte.
  if (to.name === "diagnostic" && loggedIn.value && me.value?.auth_enabled && !me.value.is_owner) {
    return { path: "/compte" };
  }
  // Les Réglages, à chaque passage, même quand seule la rubrique change (un ancien lien dans la page).
  if (to.name === "settings" && loggedIn.value) {
    const next = settingsEntry(to);
    if (next !== true) return next;
  }
  if (loggedIn.value || PUBLIC_ROUTES.has(String(to.name))) return true;
  return { name: "login", query: { suite: to.fullPath } };
});

// Retour à la dernière page de la rubrique Candidatures depuis le menu (docs/19). À l'arrivée
// sur une autre page, sa transition si elle charge des données (docs/61 §2) ; pas en changeant
// seulement un filtre, un mois ou un onglet dans la page.
// Le titre de l'onglet du navigateur, « Page · jobA1 » (WCAG 2.4.2, audit du 22.10.2026).
const PAGE_TITLES: Record<string, string> = {
  today: "Aujourd'hui",
  assistant: "Assistant",
  offers: "Offres",
  applications: "Suivi",
  alerts: "Alertes",
  insights: "Bilan",
  "orp-meeting": "Rendez-vous ORP",
  "orp-fiche": "Pour l'ORP",
  preparation: "Préparer",
  trainings: "Formations",
  profile: "Profil",
  settings: "Réglages",
  diagnostic: "État du service",
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
  "getemall-authorize": "Relier Get'emAll",
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
