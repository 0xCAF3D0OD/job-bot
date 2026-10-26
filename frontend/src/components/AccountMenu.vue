<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { useProfiles } from "../composables/useProfiles";
import AppIcon from "./AppIcon.vue";

// Menu du compte (docs/19 §1, docs/89) : dans la capsule à droite, sous ton initiale. Il porte
// ce qui n'est pas la recherche : Profil, Réglages, Données personnelles, Diagnostic, la collecte, le
// profil affiché et la déconnexion. Toujours là, sur ordinateur comme sur téléphone.
const route = useRoute();
const router = useRouter();
const { me, logout } = useAuth();
const { list, current, load, choose } = useProfiles();
const { running, collectNow } = useCollect();
// Un bouton rond, sans capsule (1.6.46) : le menu s'ouvre sous lui.
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const panel = ref<HTMLElement | null>(null);

const initial = computed(() => me.value?.username?.trim().charAt(0).toUpperCase() ?? "");

function onChange(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}

async function collect(): Promise<void> {
  open.value = false;
  await collectNow();
}

async function signOut(): Promise<void> {
  open.value = false;
  await logout();
  await router.push({ name: "news" });
}

function items(): HTMLElement[] {
  return Array.from(panel.value?.querySelectorAll<HTMLElement>("[role=menuitem]") ?? []);
}

async function toggle(): Promise<void> {
  open.value = !open.value;
  if (open.value) {
    await nextTick();
    items()[0]?.focus({ preventScroll: true });
  }
}

function close(focus = false): void {
  open.value = false;
  if (focus) trigger.value?.focus();
}

// Au clavier : les flèches parcourent les lignes, Échap ferme et rend le focus à l'initiale.
function onPanelKeydown(event: KeyboardEvent): void {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  event.preventDefault();
  const lines = items();
  const index = lines.indexOf(document.activeElement as HTMLElement);
  const step = event.key === "ArrowDown" ? 1 : -1;
  lines[(index + step + lines.length) % lines.length]?.focus();
}

function onDocumentClick(event: MouseEvent): void {
  const target = event.target as Node;
  if (open.value && root.value && !root.value.contains(target) && !panel.value?.contains(target)) open.value = false;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && open.value) close(true);
}

// Une page choisie ferme le menu.
watch(
  () => route.fullPath,
  () => (open.value = false),
);

onMounted(() => {
  void load();
  document.addEventListener("click", onDocumentClick);
  document.addEventListener("keydown", onKeydown);
});
onUnmounted(() => {
  document.removeEventListener("click", onDocumentClick);
  document.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <div
    ref="root"
    class="account-menu"
  >
    <!-- L'initiale seule, dans un rond neutre (1.6.46) : ni nom, ni flèche, ni anneau (on le
         confondait avec le focus). La légende reprend le nom accessible (WCAG 1.4.13). -->
    <button
      ref="trigger"
      type="button"
      class="header-round account-trigger"
      :aria-expanded="open"
      aria-haspopup="menu"
      :aria-label="me?.username ? `Compte : ${me.username}` : 'Compte'"
      :data-label="me?.username ? `Compte : ${me.username}` : 'Compte'"
      data-test="account-menu"
      @click="toggle"
    >
      <span
        v-if="initial"
        class="account-initial"
        aria-hidden="true"
      >{{ initial }}</span>
      <AppIcon
        v-else
        name="user"
      />
    </button>
    <div
      v-if="open"
      ref="panel"
      class="account-panel"
      role="menu"
      aria-label="Compte"
      data-test="account-panel"
      @keydown="onPanelKeydown"
    >
      <p
        v-if="me?.username"
        class="account-name"
      >
        Connecté : <strong>{{ me.username }}</strong>
      </p>
      <label
        v-if="list && list.items.length > 1"
        class="account-profile"
      >Profil affiché
        <select
          :value="current?.id"
          data-test="profile-switcher"
          @change="onChange"
        >
          <option
            v-for="profile in list.items"
            :key="profile.id"
            :value="profile.id"
          >
            {{ profile.name }} {{ profile.is_main ? "(principal)" : "(essai)" }}
          </option>
        </select>
      </label>
      <RouterLink
        to="/profil"
        role="menuitem"
        data-test="account-profile"
      >
        <span class="with-icon"><AppIcon name="user" />Profil</span>
      </RouterLink>
      <RouterLink
        to="/reglages"
        role="menuitem"
        data-test="account-settings"
      >
        <span class="with-icon"><AppIcon name="settings" />Réglages</span>
      </RouterLink>
      <RouterLink
        to="/tes-donnees"
        role="menuitem"
        data-test="account-privacy"
      >
        <span class="with-icon"><AppIcon name="shield" />Données personnelles</span>
      </RouterLink>
      <!-- Le Diagnostic technique, à l'exploitant seulement (docs/108 §3). -->
      <RouterLink
        v-if="me?.is_owner || (me?.auth_enabled === false && !me?.demo)"
        to="/reglages/diagnostic"
        role="menuitem"
        data-test="account-diagnostic"
      >
        <span class="with-icon"><AppIcon name="activity" />Diagnostic</span>
      </RouterLink>
      <!-- La démo ne collecte rien (docs/72). -->
      <button
        v-if="!me?.demo"
        type="button"
        class="link"
        role="menuitem"
        :disabled="running"
        data-test="account-collect"
        @click="collect"
      >
        <span class="with-icon"><AppIcon name="refresh" />Collecter maintenant</span>
      </button>
      <!-- Fermer son compte (docs/105) : mène à la confirmation, dans Réglages › Compte. Ni
             l'exploitant, ni la démo, ni sans connexion : ils ne peuvent pas le fermer. -->
      <RouterLink
        v-if="me?.auth_enabled && !me.is_owner && !me.demo"
        :to="{ path: '/reglages', query: { rubrique: 'compte', fermer: '1' } }"
        active-class=""
        exact-active-class=""
        role="menuitem"
        data-test="account-close"
      >
        <span class="with-icon"><AppIcon name="close" />Fermer mon compte</span>
      </RouterLink>
      <button
        v-if="me?.auth_enabled"
        type="button"
        class="link account-logout"
        role="menuitem"
        data-test="logout"
        @click="signOut"
      >
        <span class="with-icon"><AppIcon name="logout" />Se déconnecter</span>
      </button>
    </div>
  </div>
</template>
