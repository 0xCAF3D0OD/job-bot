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

// Extension du navigateur (docs/25 §4, docs/71) : installée depuis la boutique de Mozilla, reliée
// en un clic (« Relier ce navigateur ») ; le jeton à copier reste, replié.
// La fiche de la boutique, en ligne depuis le 2026-10-21 (docs/71 §8) ; vide : le mode d'emploi.
const STORE_URL = "https://addons.mozilla.org/addon/joba1-remplir-mes-candidatures/";
type Token = components["schemas"]["TokenOut"];

const tokens = ref<Token[]>([]);
const created = ref<string | null>(null);
const copied = ref(false);
const origin = globalThis.location?.origin ?? "";

async function load(): Promise<void> {
  const { data } = await api.GET("/api/extension-tokens");
  tokens.value = data ?? [];
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

function day(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleDateString("fr-CH", { day: "numeric", month: "short" }) : "jamais";
}

onMounted(load);
</script>

<template>
  <div
    class="form-card sites-card"
    data-test="extension-panel"
  >
    <fieldset>
      <legend>
        Extension du navigateur
      </legend>
      <!-- La description toujours visible, comme les CFF (docs/110). -->
      <p class="setting-desc">
        Elle remplit tes candidatures et tes codes, sans envoyer de candidature.
      </p>
      <ol class="extension-steps">
        <li>
          <a
            v-if="STORE_URL"
            :href="STORE_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="button-link"
            data-test="extension-install"
          ><span class="with-icon"><AppIcon name="external" />Installer l'extension (Firefox)<span class="visually-hidden"> (nouvel onglet)</span></span></a>
          <template v-else>
            Installe l'extension : voir « Comment l'installer ».
          </template>
        </li>
        <li>
          Un onglet « Relier jobA1 » s'ouvre : indique <code>{{ origin }}</code>, puis « Relier », et
          « Relier ce navigateur » sur la page qui s'ouvre.
        </li>
      </ol>
      <MoreInfo
        v-if="!STORE_URL"
        label="Comment l'installer"
      >
        <!-- En étapes, par navigateur (retour du 2026-10-20 : le texte d'un bloc était illisible). -->
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
      <template v-if="tokens.length">
        <p class="extension-tokens-title">
          Navigateurs reliés
        </p>
        <ul class="extension-tokens">
          <li
            v-for="token in tokens"
            :key="token.id"
          >
            <span>{{ token.name }} <span class="muted">· utilisé {{ day(token.last_used_at) }}</span></span>
            <IconButton
              icon="trash"
              :label="`Révoquer ${token.name}`"
              danger
              data-test="extension-revoke"
              @click="revoke(token)"
            />
          </li>
        </ul>
      </template>
      <MoreInfo label="Relier avec un jeton">
        <p>Si « Relier » ne fonctionne pas : crée un jeton, puis colle-le dans l'extension (« Relier avec un jeton »).</p>
        <div
          v-if="created"
          class="extension-token"
          data-test="extension-token"
        >
          <code>{{ created }}</code>
          <button
            type="button"
            class="link"
            @click="copy"
          >
            <CopyLabel :done="copied" />
          </button>
          <p class="hint">
            Montré une seule fois : colle-le maintenant dans l'extension.
          </p>
        </div>
        <div class="form-actions">
          <button
            type="button"
            class="secondary small"
            data-test="extension-create"
            @click="create"
          >
            <span class="with-icon"><AppIcon name="plus" />Créer un jeton</span>
          </button>
        </div>
      </MoreInfo>
    </fieldset>
  </div>
</template>
