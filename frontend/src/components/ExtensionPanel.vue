<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { browserName } from "../browserName";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import MoreInfo from "./MoreInfo.vue";
import CopyLabel from "./CopyLabel.vue";
import { offerUndo } from "../composables/useUndo";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Extension du navigateur (docs/25 §4, docs/71) : installée depuis la boutique de Mozilla, reliée
// en un clic (« Relier ce navigateur ») ; le jeton à copier reste, en secours.
// La fiche de la boutique, en ligne depuis le 2026-10-21 (docs/71 §8) ; vide : le mode d'emploi.
const STORE_URL = "https://addons.mozilla.org/addon/joba1-remplir-mes-candidatures/";
type Token = components["schemas"]["TokenOut"];

const tokens = ref<Token[]>([]);
const created = ref<string | null>(null);
const copied = ref(false);
const origin = globalThis.location?.origin ?? "";

async function load(): Promise<void> {
  const { data } = await api.GET("/api/extension-tokens");
  tokens.value = Array.isArray(data) ? data : [];
}

async function create(): Promise<void> {
  const { data } = await api.POST("/api/extension-tokens", { body: { name: browserName(), link: false } });
  if (!data) return;
  created.value = data.token;
  copied.value = false;
  await load();
}

// Révoqué au bout de 6 s, « Annuler » d'ici là (docs/108 §1).
async function revoke(token: Token): Promise<void> {
  const before = tokens.value;
  tokens.value = before.filter((t) => t.id !== token.id);
  await offerUndo({
    message: `« ${token.name} » révoqué : l'extension ne remplira plus`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/extension-tokens/{token_id}", { params: { path: { token_id: token.id } }, keepalive });
      if (error !== undefined) return false;
      await load();
    },
    restore: () => {
      tokens.value = before;
    },
  });
}

async function copy(): Promise<void> {
  if (!created.value) return;
  try {
    await navigator.clipboard.writeText(created.value);
    copied.value = true;
  } catch {
    copied.value = false;
  }
}

// « Navigateur relié · utilisé le 15 oct. » (texte seul, sans icône).
function lastUsed(token: Token): string {
  if (!token.last_used_at) return "Navigateur relié · pas encore utilisé.";
  return `Navigateur relié · utilisé le ${new Date(token.last_used_at).toLocaleDateString("fr-CH", { day: "numeric", month: "short" })}.`;
}

onMounted(load);
</script>

<template>
  <!-- L'extension (1.6.67, planche « 5. Réglages ») : l'installer, la relier, puis une ligne par
       navigateur relié et le jeton de secours, dans la même carte (loi de proximité). -->
  <SettingCard
    class="sites-card"
    data-test="extension-panel"
  >
    <!-- La description toujours visible, comme les CFF (docs/110). -->
    <SettingRow
      title="Extension du navigateur"
      description="Elle remplit tes candidatures et tes codes dans Firefox, sans envoyer de candidature."
    >
      <a
        v-if="STORE_URL"
        :href="STORE_URL"
        target="_blank"
        rel="noopener noreferrer"
        class="button-link"
        data-test="extension-install"
      ><span class="with-icon"><AppIcon name="external" />Installer l'extension<span class="visually-hidden"> (Firefox, nouvel onglet)</span></span></a>
    </SettingRow>
    <SettingRow
      title="Relier l'extension"
      :description="`Dans l'onglet « Relier jobA1 » qui s'ouvre, indique ${origin}, puis « Relier » et « Relier ce navigateur ».`"
    />
    <SettingRow
      v-for="token in tokens"
      :key="token.id"
      :title="token.name"
      :description="lastUsed(token)"
    >
      <IconButton
        icon="trash"
        :label="`Révoquer ${token.name}`"
        danger
        data-test="extension-revoke"
        @click="revoke(token)"
      />
    </SettingRow>
    <SettingRow
      title="Relier avec un jeton"
      description="Si « Relier » ne marche pas : crée un jeton et colle-le dans l'extension."
    >
      <button
        type="button"
        class="secondary small"
        data-test="extension-create"
        @click="create"
      >
        <span class="with-icon"><AppIcon name="plus" />Créer un jeton</span>
      </button>
    </SettingRow>
    <SettingRow
      v-if="created"
      title="Nouveau jeton"
      description="Montré une seule fois : colle-le maintenant dans l'extension."
      wide
    >
      <div
        class="extension-token"
        data-test="extension-token"
      >
        <code>{{ created }}</code>
        <button
          type="button"
          class="link"
          @click="copy"
        >
          <CopyLabel
            :done="copied"
            label="Copier le jeton"
          />
        </button>
      </div>
    </SettingRow>
  </SettingCard>
  <!-- Sans fiche de boutique : les étapes par navigateur, repliées sous la carte (retour du
       2026-10-20 : le texte d'un bloc était illisible). -->
  <MoreInfo
    v-if="!STORE_URL"
    label="Comment l'installer"
  >
    <p class="install-browser">
      Firefox
    </p>
    <ol class="install-steps">
      <li>Dans le dépôt : <code>make extension</code>.</li>
      <li>Ouvre <code>about:debugging#/runtime/this-firefox</code>.</li>
      <li>« Charger un module complémentaire temporaire », puis choisis <code>extension/web-ext-artifacts/joba1-….zip</code>.</li>
      <li>À refaire après chaque redémarrage de Firefox.</li>
    </ol>
    <p class="install-browser">
      Chrome, Edge ou Brave
    </p>
    <ol class="install-steps">
      <li>Ouvre <code>chrome://extensions</code>.</li>
      <li>Active le mode développeur.</li>
      <li>« Charger l'extension non empaquetée », puis choisis le dossier <code>extension/</code>.</li>
    </ol>
  </MoreInfo>
</template>
