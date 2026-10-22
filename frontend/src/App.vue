<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppFooter from "./components/AppFooter.vue";
import { DEMO_REFUSED_EVENT, UNAUTHORIZED_EVENT } from "./api/client";

import NotificationBell from "./components/NotificationBell.vue";
import AccountMenu from "./components/AccountMenu.vue";
import AppIcon from "./components/AppIcon.vue";
import BrandMark from "./components/BrandMark.vue";
import HeaderCapsule from "./components/HeaderCapsule.vue";
import TabBar from "./components/TabBar.vue";
import AssistantPanel from "./components/AssistantPanel.vue";
import AppToast from "./components/AppToast.vue";
import UndoToast from "./components/UndoToast.vue";
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
  nextAt: maintenanceNextAt,
  retry: maintenanceRetry,
} = useMaintenance();

const { start: startNewsCount } = useNewsCount();
const { current: profile, main: mainProfile, choose } = useProfiles();
const route = useRoute();
// Fichiers préparés : le retour sur le lien lui-même (docs/59 §4).
useFileDownloads();
const router = useRouter();
const { me, loggedIn, load, expired } = useAuth();
const { last: lastJobsPage, check: checkJobsPage } = useJobsMemory();
// Le menu ne mène jamais à une offre disparue (audit du 22.10.2026).
watch(loggedIn, (now) => now && void checkJobsPage().catch(() => undefined), { immediate: true });
// Cinq entrées (docs/19 §1, docs/89) ; sans connexion, seulement la présentation (docs/67).
const DISCOVER: NavEntry[] = [{ path: "/la-plateforme", name: "discover", label: "La plateforme", icon: "globe" }];
const menu = computed(() => (loggedIn.value ? mainMenu : DISCOVER));
// La page en cours dans le menu : Candidatures couvre tous ses onglets et ses fiches.
function isCurrent(entry: NavEntry): boolean {
  if (entry.name === "jobs") return route.path.startsWith("/candidatures");
  if (entry.name === "bilan") return route.path.startsWith("/bilan");
  return route.path === entry.path || route.path.startsWith(`${entry.path}/`);
}

function skipToContent(): void {
  document.getElementById("contenu")?.focus();
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
  <!-- Le premier arrêt au clavier saute l'en-tête, le bandeau et le menu (WCAG 2.4.1, audit du
       22.10.2026) ; visible seulement quand il a le focus. -->
  <a
    class="skip-link"
    href="#contenu"
    data-test="skip-link"
    @click.prevent="skipToContent"
  >Aller au contenu</a>
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
        <!-- Le logo, le visage du 1, et « jobA1 » en entier, connecté ou non (docs/103). -->
        <BrandMark :size="32" />
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
        <!-- La capsule (docs/89, docs/91, docs/92) : la cloche et ton initiale ; elle se déroule pour
             montrer ce qu'on ouvre. Le livre de Progresser l'a quittée : Formations et Actualités
             sont dans le Bilan (docs/126 §1). -->
        <HeaderCapsule>
          <NotificationBell />
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
      <span class="with-icon"><AppIcon name="arrow-left" />Revenir à {{ mainProfile.name }}</span>
    </button>
  </div>
  <div
    v-if="me?.demo && !route.meta.bare"
    class="demo-banner"
    role="region"
    aria-label="Démo"
    data-test="demo-banner"
  >
    <strong>Démo</strong>
    <span>Données fictives : rien de ce que tu fais n'est enregistré.</span>
    <RouterLink to="/la-plateforme">
      Découvrir jobA1
    </RouterLink>
  </div>
  <!-- Le bandeau « Annuler » (docs/108 §1). -->
  <UndoToast />
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
  <main
    id="contenu"
    tabindex="-1"
  >
    <RouterView />
  </main>
  <AppFooter v-if="!route.meta.bare" />
  <!-- Sur téléphone, les deux pages de travail en bas de l'écran (docs/92). -->
  <TabBar v-if="loggedIn" />
  <MaintenanceOverlay
    :waiting="maintenanceWaiting"
    :message="maintenanceMessage"
    :next-at="maintenanceNextAt"
    @retry="maintenanceRetry"
  />
  <PageTransition />
  <AssistantPanel v-if="loggedIn && !route.meta.bare" />
</template>
