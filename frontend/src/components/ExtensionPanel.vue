<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import MoreInfo from "./MoreInfo.vue";

// Extension du navigateur (docs/25 §4) : un jeton révocable la relie à la plateforme.
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
  const { data } = await api.POST("/api/extension-tokens", { body: { name: navigatorName() } });
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

function navigatorName(): string {
  const agent = globalThis.navigator?.userAgent ?? "";
  if (agent.includes("Edg/")) return "Edge";
  if (agent.includes("Brave")) return "Brave";
  if (agent.includes("Chrome/")) return "Chrome";
  return "Mon navigateur";
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
      <legend>Extension du navigateur</legend>
      <p class="hint">
        Remplit le formulaire de l'employeur avec tes données ; tu vérifies et tu envoies toi-même.
      </p>
      <MoreInfo label="Comment l'installer">
        <ol class="extension-steps">
          <li>
            Chrome, Edge ou Brave : <code>chrome://extensions</code>, mode développeur, « Charger l'extension non
            empaquetée » → le dossier <code>extension/</code> du dépôt. Firefox : voir <code>extension/README.md</code>.
          </li>
          <li>Crée un jeton ci-dessous, puis clique sur l'icône job-bot : colle <code>{{ origin }}</code> et le jeton.</li>
        </ol>
      </MoreInfo>
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
          {{ copied ? "Copié" : "Copier" }}
        </button>
        <p class="hint">
          Montré une seule fois : colle-le maintenant dans l'extension.
        </p>
      </div>
      <ul
        v-if="tokens.length"
        class="extension-tokens"
      >
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
    </fieldset>
  </div>
</template>
