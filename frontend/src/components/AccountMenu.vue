<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useProfiles } from "../composables/useProfiles";
import AppIcon from "./AppIcon.vue";

// Menu du compte (docs/19 §1, docs/89) : sous ton initiale, en haut à droite sur ordinateur. Il ne garde que
// « Compte » et « Se déconnecter » (décision de Kevin du 2026-11-05, C2) : le Profil, les Réglages, la collecte,
// le profil affiché et le reste s'ouvrent depuis la page Compte.
const route = useRoute();
const router = useRouter();
const { me, logout } = useAuth();
// Le profil affiché est lu dès l'ouverture de l'app (le bandeau « Revenir à … »).
const { load } = useProfiles();
// Un bouton rond, sans capsule (1.6.46) : le menu s'ouvre sous lui.
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const panel = ref<HTMLElement | null>(null);

const initial = computed(() => me.value?.username?.trim().charAt(0).toUpperCase() ?? "");

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
      <RouterLink
        to="/compte"
        role="menuitem"
        data-test="account-page-link"
      >
        <span class="with-icon"><AppIcon name="user" />Compte</span>
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
