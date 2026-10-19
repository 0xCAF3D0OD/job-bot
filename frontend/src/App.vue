<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { DEMO_REFUSED_EVENT, UNAUTHORIZED_EVENT } from "./api/client";

import NotificationBell from "./components/NotificationBell.vue";
import AccountMenu from "./components/AccountMenu.vue";
import BrandMark from "./components/BrandMark.vue";
import HeaderCapsule from "./components/HeaderCapsule.vue";
import ProgressPreview from "./components/ProgressPreview.vue";
import TabBar from "./components/TabBar.vue";
import AssistantPanel from "./components/AssistantPanel.vue";
import AppToast from "./components/AppToast.vue";
import PageTransition from "./components/PageTransition.vue";
import MaintenanceOverlay from "./components/MaintenanceOverlay.vue";
import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { useNewsCount } from "./composables/useNewsCount";
import { useCollect } from "./composables/useCollect";
import { useFileDownloads } from "./composables/useFileDownloads";
import { useMaintenance } from "./composables/useMaintenance";
import { useProfiles } from "./composables/useProfiles";
import { mainMenu, type NavEntry, PUBLIC_ROUTES } from "./router";

const { message, failed } = useCollect();
// Maintenance (docs/79) : la page d'attente, et le rappel à l'exploitant qui passe quand même.
const {
  waiting: maintenanceWaiting,
  message: maintenanceMessage,
  bypass: maintenanceBypass,
  reading: maintenanceReading,
  refused: maintenanceRefused,
} = useMaintenance();

const { start: startNewsCount } = useNewsCount();
const { current: profile, main: mainProfile, choose } = useProfiles();
const route = useRoute();
// Fichiers préparés : le retour sur le lien lui-même (docs/59 §4).
useFileDownloads();
const router = useRouter();
const { me, loggedIn, load, expired } = useAuth();
const { last: lastJobsPage } = useJobsMemory();
// Cinq entrées (docs/19 §1, docs/89) ; sans connexion, seulement la présentation (docs/67).
const DISCOVER: NavEntry[] = [{ path: "/la-plateforme", name: "discover", label: "La plateforme" }];
const menu = computed(() => (loggedIn.value ? mainMenu : DISCOVER));
// La page en cours dans le menu : Candidatures couvre tous ses onglets et ses fiches.
function isCurrent(entry: NavEntry): boolean {
  if (entry.name === "jobs") return route.path.startsWith("/candidatures");
  return route.path === entry.path || route.path.startsWith(`${entry.path}/`);
}

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
        <!-- Le logo et « jobA1 » en entier, connecté ou non (docs/98). -->
        <BrandMark :size="28" />
        jobA1
      </RouterLink>
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
              {{ entry.label }}
            </RouterLink>
          </li>
        </ul>
      </nav>
      <div
        v-if="loggedIn"
        class="topbar-actions"
      >
        <!-- La capsule (docs/89, docs/91, docs/92) : la cloche, l'étincelle de Progresser et ton
             initiale ; elle se déroule pour montrer ce qu'on ouvre. -->
        <HeaderCapsule>
          <NotificationBell />
          <span
            class="capsule-sep"
            aria-hidden="true"
          />
          <ProgressPreview />
          <span
            class="capsule-sep"
            aria-hidden="true"
          />
          <AccountMenu />
        </HeaderCapsule>
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
  <p
    v-if="maintenanceBypass"
    class="maintenance-bypass"
    role="status"
    data-test="maintenance-bypass"
  >
    Maintenance annoncée : la plateforme est fermée aux autres comptes. Pour la rouvrir :
    <code>jobbot maintenance off</code>.
  </p>
  <p
    v-else-if="maintenanceReading"
    class="maintenance-bypass reading"
    role="status"
    data-test="maintenance-reading"
  >
    Maintenance : tu peux consulter, pas encore enregistrer.{{ maintenanceMessage ? ` ${maintenanceMessage}` : "" }}
  </p>
  <AppToast
    v-if="maintenanceRefused"
    :message="maintenanceRefused"
    data-test="maintenance-refused"
    @close="maintenanceRefused = ''"
  />
  <main>
    <RouterView />
  </main>
  <!-- Sur téléphone, les deux pages de travail en bas de l'écran (docs/92). -->
  <TabBar v-if="loggedIn" />
  <MaintenanceOverlay
    :waiting="maintenanceWaiting"
    :message="maintenanceMessage"
  />
  <PageTransition />
  <AssistantPanel v-if="loggedIn && !route.meta.bare" />
</template>
