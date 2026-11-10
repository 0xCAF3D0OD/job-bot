<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useJobsMemory } from "../composables/useJobsMemory";
import { mainMenu, type NavEntry } from "../router";
import AccountMenu from "./AccountMenu.vue";
import AppIcon from "./AppIcon.vue";
import BrandMark from "./BrandMark.vue";
import GlobalSearch from "./GlobalSearch.vue";
import NotificationBell from "./NotificationBell.vue";

// L'en-tête. Sur ordinateur, inchangé : logo, menu, recherche, cloche, compte.
// Sur téléphone (sous 820 px), celui des maquettes (docs/139, décision du 2026-11-02, maquettes strictes) :
// - Accueil : le logo et la cloche ;
// - une page d'onglet (Candidatures, Bilan, Réglages, Profil) : le logo et le titre de la page, à 30 px ;
// - les autres pages : le logo seul, en attendant la variante « retour + titre » de chaque écran.
// Ni loupe ni menu du compte : la recherche ira dans Candidatures, le compte est un onglet de la barre du bas.
const route = useRoute();
const { me, loggedIn } = useAuth();
const { last: lastJobsPage } = useJobsMemory();

// Cinq entrées (docs/19 §1, docs/89) ; sans connexion, seulement la présentation (docs/67).
const DISCOVER: NavEntry[] = [{ path: "/la-plateforme", name: "discover", label: "La plateforme", icon: "globe" }];
const menu = computed(() => (loggedIn.value ? mainMenu : DISCOVER));
// La page en cours dans le menu : Candidatures couvre tous ses onglets et ses fiches.
function isCurrent(entry: NavEntry): boolean {
  if (entry.name === "jobs") return route.path.startsWith("/candidatures");
  if (entry.name === "bilan") return route.path.startsWith("/bilan");
  return route.path === entry.path || route.path.startsWith(`${entry.path}/`);
}

// Une fiche ouverte (offre, candidature) ou une rubrique des Réglages est une sous-page : pas de titre d'onglet. Le
// Profil aussi (maquette ProfilTel, PR 20) : il a sa barre « ← Mon profil », sous le Compte.
const SUB_PAGE = ["offre", "candidature", "rubrique"];
const phoneTitle = computed<string | null>(() => {
  if (!loggedIn.value || SUB_PAGE.some((key) => route.query[key])) return null;
  if (route.path.startsWith("/candidatures") && route.meta.tab) return "Candidatures";
  if (route.path.startsWith("/bilan") && route.meta.tab) return "Bilan";
  if (route.name === "account") return "Compte";
  if (route.name === "settings") return "Réglages";
  return null;
});
const variant = computed(() => {
  if (!loggedIn.value) return "public";
  if (route.name === "today") return "home";
  return phoneTitle.value ? "tab" : "page";
});

// La ligne du bas de l'en-tête (1.6.37) : seulement quand le contenu défile sous l'en-tête fixe.
const scrolled = ref(false);
function onScroll(): void {
  scrolled.value = window.scrollY > 0;
}
onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});
onUnmounted(() => window.removeEventListener("scroll", onScroll));
</script>

<template>
  <header
    :class="['topbar', { 'has-burger': loggedIn, scrolled }]"
    :data-variant="variant"
    data-test="app-header"
  >
    <div class="topbar-inner">
      <RouterLink
        to="/"
        class="brand"
        aria-label="jobA1, accueil"
      >
        <!-- Le logo, le visage du 1, et « jobA1 » en entier, connecté ou non (docs/103) ; sur téléphone, le logo seul. -->
        <BrandMark :size="32" />
        <span class="brand-name">jobA1</span>
      </RouterLink>
      <!-- Le titre de la page d'onglet sur téléphone. Le h1 de la page reste pour les lecteurs d'écran. -->
      <p
        v-if="phoneTitle"
        class="topbar-title"
        aria-hidden="true"
        data-test="header-title"
      >
        {{ phoneTitle }}
      </p>
      <nav
        class="main-nav"
        aria-label="Navigation principale"
      >
        <ul class="nav">
          <li
            v-for="entry in menu"
            :key="entry.name"
          >
            <RouterLink
              :to="entry.name === 'jobs' ? lastJobsPage : entry.path"
              :class="{ 'router-link-active': isCurrent(entry) }"
              :aria-current="isCurrent(entry) ? 'page' : undefined"
            >
              <!-- L'icône devant le nom (docs/101, règle 1). -->
              <span class="with-icon">
                <AppIcon
                  v-if="entry.icon"
                  :name="entry.icon"
                />{{ entry.label }}
              </span>
            </RouterLink>
          </li>
        </ul>
      </nav>
      <div
        v-if="loggedIn"
        class="topbar-actions"
      >
        <!-- Deux boutons ronds, sans capsule (1.6.46) : la cloche et l'initiale ; chacun ouvre son menu
             sous lui, au clic, et se ferme à Échap ou par un clic ailleurs. La recherche globale (série du
             27.10, point 2) : le champ à gauche de la cloche. Sur téléphone, la cloche seule, sur l’Accueil. -->
        <!-- Les liens et outils d'une page d'onglet, sur téléphone (Candidatures : « Alertes », filtres). -->
        <div
          id="topbar-page-tools"
          class="topbar-page-tools"
        />
        <GlobalSearch />
        <NotificationBell />
        <AccountMenu />
      </div>
      <div
        v-else-if="me"
        class="topbar-actions"
      >
        <RouterLink
          :to="{ name: 'login', query: route.name === 'login' ? route.query : { suite: route.fullPath } }"
          class="button-link primary-link"
          data-test="login-link"
        >
          Se connecter
        </RouterLink>
      </div>
    </div>
  </header>
</template>
