<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { DEMO_REFUSED_EVENT, UNAUTHORIZED_EVENT } from "./api/client";

import NotificationBell from "./components/NotificationBell.vue";
import BrandFigure from "./components/BrandFigure.vue";
import AccountMenu from "./components/AccountMenu.vue";
import MobileMenu from "./components/MobileMenu.vue";
import AssistantPanel from "./components/AssistantPanel.vue";
import AppToast from "./components/AppToast.vue";
import PageTransition from "./components/PageTransition.vue";
import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { useNewsCount } from "./composables/useNewsCount";
import { useCollect } from "./composables/useCollect";
import { useFileDownloads } from "./composables/useFileDownloads";
import { useProfiles } from "./composables/useProfiles";
import { navigation, type NavEntry, PUBLIC_ROUTES } from "./router";

const { message, running, failed, collectNow } = useCollect();

const { count: newsCount, start: startNewsCount } = useNewsCount();
const { current: profile, main: mainProfile, choose } = useProfiles();
const route = useRoute();
// Fichiers préparés : le retour sur le lien lui-même (docs/59 §4).
useFileDownloads();
const router = useRouter();
const { me, loggedIn, load, expired } = useAuth();
const { last: lastJobsPage } = useJobsMemory();
// Six entrées (docs/19 §1) ; sans connexion, seulement la présentation de la plateforme (docs/67).
const DISCOVER: NavEntry[] = [{ path: "/la-plateforme", name: "discover", label: "La plateforme" }];
const menu = computed(() => (loggedIn.value ? navigation : DISCOVER));

function onUnauthorized(): void {
  expired();
  if (!PUBLIC_ROUTES.has(String(route.name))) {
    void router.push({ name: "login", query: { suite: route.fullPath } });
  }
}


// Démo publique (docs/72) : une action refusée le dit, au lieu d'une erreur.
const demoRefused = ref("");
function onDemoRefused(event: Event): void {
  demoRefused.value = String((event as CustomEvent<string>).detail || "Dans la démo, rien n'est enregistré.");
}

onMounted(async () => {
  window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  window.addEventListener(DEMO_REFUSED_EVENT, onDemoRefused);
  await load();
  // Le compteur des Actualités, une fois connecté seulement : sans connexion, elles ne
  // répondent plus (docs/69 §1).
  watch(loggedIn, (yes) => yes && startNewsCount(), { immediate: true });
});
onUnmounted(() => {
  window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  window.removeEventListener(DEMO_REFUSED_EVENT, onDemoRefused);
});
</script>

<template>
  <header
    v-if="!route.meta.bare"
    :class="['topbar', { 'has-burger': loggedIn }]"
  >
    <div class="topbar-inner">
      <RouterLink
        to="/"
        class="brand"
        aria-label="jobA1, accueil"
      >
        <span
          class="brand-mark"
          aria-hidden="true"
        />
        <!-- Connecté : le « 1 » devient le personnage de l'heure (docs/68). -->
        <span
          v-if="loggedIn"
          class="brand-name"
        >jobA<BrandFigure /></span>
        <template v-else>
          jobA1
        </template>
      </RouterLink>
      <nav aria-label="Navigation principale">
        <ul class="nav">
          <li
            v-for="entry in menu"
            :key="entry.name"
          >
            <RouterLink
              :to="entry.name === 'jobs' ? lastJobsPage : entry.path"
              :class="{ 'router-link-active': entry.name === 'jobs' && route.path.startsWith('/candidatures') }"
            >
              {{ entry.label }}
              <span
                v-if="entry.name === 'news' && newsCount"
                class="nav-count"
                data-test="news-count"
              >{{ newsCount }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>
      <div
        v-if="loggedIn"
        class="topbar-actions"
      >
        <NotificationBell />
        <!-- La démo ne collecte rien (docs/72). -->
        <button
          v-if="!me?.demo"
          type="button"
          class="secondary small collect-top"
          :disabled="running"
          data-test="collect-top"
          @click="collectNow"
        >
          Collecter
        </button>
        <AccountMenu />
        <MobileMenu
          :menu="menu"
          :news-count="newsCount"
        />
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
    <!-- Carte des alertes (cloche), sous la barre et à sa largeur. -->
    <div
      id="bell-drop"
      class="bell-drop"
    />
  </header>
  <div
    v-if="loggedIn && profile && !profile.is_main"
    class="profile-banner"
    role="status"
    data-test="profile-banner"
  >
    <strong>Profil d'essai : {{ profile.name }}</strong>
    <span>Seules les Actualités et les Formations suivent ce profil ; les autres pages restent les tiennes.</span>
    <button
      v-if="mainProfile"
      type="button"
      class="link"
      data-test="profile-back"
      @click="choose(mainProfile.id)"
    >
      Revenir à {{ mainProfile.name }}
    </button>
  </div>
  <div
    v-if="me?.demo && !route.meta.bare"
    class="demo-banner"
    role="note"
    data-test="demo-banner"
  >
    <strong>Démo</strong>
    <span>Données fictives : rien de ce que tu fais n'est enregistré.</span>
    <RouterLink to="/la-plateforme">
      Découvrir jobA1
    </RouterLink>
    <a
      href="https://github.com/0xCAF3D0OD/job-bot"
      target="_blank"
      rel="noopener noreferrer"
    >Le code</a>
  </div>
  <AppToast
    v-if="demoRefused"
    :message="demoRefused"
    data-test="demo-refused"
    @close="demoRefused = ''"
  />
  <AppToast
    v-if="message"
    :message="message"
    :error="failed"
    @close="message = ''"
  />
  <main>
    <RouterView />
  </main>
  <PageTransition />
  <AssistantPanel v-if="loggedIn && !route.meta.bare" />
</template>
