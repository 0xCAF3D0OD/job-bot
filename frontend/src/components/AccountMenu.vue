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
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const panel = ref<HTMLElement | null>(null);

const initial = computed(() => me.value?.username?.trim().charAt(0).toUpperCase() ?? "");
// Une page du menu ouverte : l'initiale est marquée comme active.
const active = computed(() => ["/profil", "/reglages", "/tes-donnees"].some((path) => route.path.startsWith(path)));

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
    items()[0]?.focus();
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
  if (open.value && root.value && !root.value.contains(event.target as Node)) open.value = false;
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
    <button
      ref="trigger"
      type="button"
      :class="['account-trigger', { active }]"
      :aria-expanded="open"
      aria-haspopup="menu"
      :aria-label="me?.username ? `Compte : ${me.username}` : 'Compte'"
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
      <AppIcon
        name="chevron"
        class="account-chevron"
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
            {{ profile.is_main ? "👤 " : "🧪 " }}{{ profile.name }}
          </option>
        </select>
      </label>
      <RouterLink
        to="/profil"
        role="menuitem"
        data-test="account-profile"
      >
        Profil
      </RouterLink>
      <RouterLink
        to="/reglages"
        role="menuitem"
        data-test="account-settings"
      >
        Réglages
      </RouterLink>
      <RouterLink
        to="/tes-donnees"
        role="menuitem"
        data-test="account-privacy"
      >
        Données personnelles
      </RouterLink>
      <RouterLink
        to="/reglages/diagnostic"
        role="menuitem"
        data-test="account-diagnostic"
      >
        Diagnostic
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
        Collecter maintenant
      </button>
      <button
        v-if="me?.auth_enabled"
        type="button"
        class="link account-logout"
        role="menuitem"
        data-test="logout"
        @click="signOut"
      >
        Se déconnecter
      </button>
    </div>
  </div>
</template>
