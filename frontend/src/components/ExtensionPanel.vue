<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { browserName } from "../browserName";
import MoreInfo from "./MoreInfo.vue";
import CopyLabel from "./CopyLabel.vue";
import HoverNote from "./HoverNote.vue";

// Extension du navigateur (docs/25 §4, docs/71) : installée depuis la boutique de Mozilla, reliée
// en un clic (« Relier ce navigateur ») ; le jeton à copier reste, replié.
// La fiche de la boutique, une fois en ligne (docs/71 §8) ; vide : le mode d'emploi.
const STORE_URL = "";
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

async function revoke(token: Token): Promise<void> {
  if (!window.confirm(`Révoquer le jeton « ${token.name} » ? L'extension reliée ne pourra plus remplir.`)) return;
  await api.DELETE("/api/extension-tokens/{token_id}", { params: { path: { token_id: token.id } } });
  await load();
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
        <HoverNote text="Elle remplit tes candidatures et Job-Room. Rien n'est envoyé à ta place.">
          Extension du navigateur
        </HoverNote>
      </legend>
      <ol class="extension-steps">
        <li>
          <a
            v-if="STORE_URL"
            :href="STORE_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="button-link"
            data-test="extension-install"
          >Installer l'extension (Firefox)</a>
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
        <p>
          Firefox : <code>make extension</code> dans le dépôt, puis <code>about:debugging#/runtime/this-firefox</code> ›
          « Charger un module complémentaire temporaire » › le fichier
          <code>extension/web-ext-artifacts/joba1-…zip</code> (à refaire après un redémarrage).
          Chrome, Edge ou Brave : <code>chrome://extensions</code>, mode développeur, « Charger l'extension non
          empaquetée » › le dossier <code>extension/</code>.
        </p>
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
            <button
              type="button"
              class="link danger"
              data-test="extension-revoke"
              @click="revoke(token)"
            >
              Révoquer
            </button>
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
            Créer un jeton
          </button>
        </div>
      </MoreInfo>
    </fieldset>
  </div>
</template>
