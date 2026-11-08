<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppFooter from "./components/AppFooter.vue";
import { DEMO_REFUSED_EVENT, UNAUTHORIZED_EVENT } from "./api/client";

import AppIcon from "./components/AppIcon.vue";
import AppHeader from "./components/AppHeader.vue";
import BottomNav from "./components/BottomNav.vue";
import AssistantPanel from "./components/AssistantPanel.vue";
import AppToast from "./components/AppToast.vue";
import UndoToast from "./components/UndoToast.vue";
import PageTransition from "./components/PageTransition.vue";
import DismissLayer from "./components/DismissLayer.vue";
import { closeAllLayers } from "./composables/useDismissLayer";
import MaintenanceOverlay from "./components/MaintenanceOverlay.vue";
import { useAuth } from "./composables/useAuth";
import { useJobsMemory } from "./composables/useJobsMemory";
import { useCollect } from "./composables/useCollect";
import { useAutoGrow } from "./composables/useAutoGrow";
import { useFileDownloads } from "./composables/useFileDownloads";
import { useMaintenance } from "./composables/useMaintenance";
import { usePhone } from "./composables/usePhone";
import { useProfiles } from "./composables/useProfiles";
import { PUBLIC_ROUTES } from "./router";

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

const { current: profile, main: mainProfile, choose } = useProfiles();
const route = useRoute();
// Fichiers préparés : le retour sur le lien lui-même (docs/59 §4).
useFileDownloads();
useAutoGrow();
const router = useRouter();
const { me, loggedIn, load, expired } = useAuth();
// Le pied de page (docs/126 §4) : sur téléphone connecté, les maquettes n'en ont pas ; il reste en bas du
// Compte, à un onglet de chaque page (nLPD : facile à trouver).
const { phone } = usePhone();
const footer = computed(() => !route.meta.bare && (!phone.value || !loggedIn.value || route.path === "/compte"));
const { check: checkJobsPage } = useJobsMemory();
// Le menu ne mène jamais à une offre disparue (audit du 22.10.2026).
watch(loggedIn, (now) => now && void checkJobsPage().catch(() => undefined), { immediate: true });
// Un changement de page ferme le panneau ou le menu ouvert (docs/143, D24).
watch(() => route.fullPath, () => closeAllLayers());
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
  <AppHeader v-if="!route.meta.bare" />
  <div
    v-if="loggedIn && profile && !profile.is_main"
    class="profile-banner"
    role="status"
    data-test="profile-banner"
  >
    <strong>Profil d'essai : {{ profile.name }}</strong>
    <span>Seules les Formations suivent ce profil ; les autres pages restent les tiennes.</span>
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
  <AppFooter v-if="footer" />
  <!-- Sur téléphone, les deux pages de travail en bas de l'écran (docs/92). -->
  <BottomNav v-if="loggedIn" />
  <MaintenanceOverlay
    :waiting="maintenanceWaiting"
    :message="maintenanceMessage"
    :next-at="maintenanceNextAt"
    @retry="maintenanceRetry"
  />
  <DismissLayer />
  <PageTransition />
  <AssistantPanel v-if="loggedIn && !route.meta.bare" />
</template>
