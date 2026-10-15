<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import HelpTip from "./HelpTip.vue";
import MoreInfo from "./MoreInfo.vue";

// Tes dates dans ton agenda (docs/40 §2) : une adresse d'abonnement à jeton secret,
// révocable ; ton agenda la relit tout seul.
type Token = components["schemas"]["CalendarTokenOut"];
const tokens = ref<Token[]>([]);
const created = ref<string | null>(null);
const copied = ref(false);
const creating = ref(false);
const createError = ref("");

async function load(): Promise<void> {
  const { data } = await api.GET("/api/agenda/tokens");
  tokens.value = data ?? [];
}

// Chaque adresse porte sa date de création (« Agenda du 15 oct. ») : on sait laquelle révoquer.
async function create(): Promise<void> {
  if (creating.value) return;
  creating.value = true;
  createError.value = "";
  try {
    const name = `Agenda du ${new Date().toLocaleDateString("fr-CH", { day: "numeric", month: "short" })}`;
    const { data } = await api.POST("/api/agenda/tokens", {
      body: { name, origin: globalThis.location?.origin ?? null },
    });
    if (!data) {
      createError.value = "Création impossible : réessaie dans un instant.";
      return;
    }
    created.value = data.url;
    copied.value = false;
    await load();
  } catch {
    createError.value = "Création impossible : réessaie dans un instant.";
  } finally {
    creating.value = false;
  }
}

async function revoke(token: Token): Promise<void> {
  if (!window.confirm(`Révoquer « ${token.name} » ? L'agenda abonné ne recevra plus tes dates.`)) return;
  await api.DELETE("/api/agenda/tokens/{token_id}", { params: { path: { token_id: token.id } } });
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
    data-test="agenda-panel"
  >
    <fieldset>
      <legend>
        Abonnement d'agenda
        <HelpTip
          text="Entretiens, suites attendues, remise des preuves ORP et relances arrivent dans ton agenda, tenus à jour. Seuls l'entreprise, le poste et la date y figurent."
          label="Aide : abonnement d'agenda"
        />
      </legend>
      <MoreInfo label="Comment l'ajouter">
        <ul class="extension-steps">
          <li><strong>iPhone</strong> : Réglages › Calendrier › Comptes › Ajouter un compte › Autre › Ajouter un calendrier avec abonnement, puis colle l'adresse.</li>
          <li><strong>Google Agenda</strong> (ordinateur) : « Autres agendas » › ＋ › « À partir de l'URL ».</li>
          <li><strong>Outlook</strong> : Ajouter un calendrier › « S'abonner à partir du web ».</li>
          <li>Google et Outlook lisent l'adresse depuis leurs serveurs : ta plateforme doit être joignable depuis Internet (ton tunnel, par exemple).</li>
        </ul>
      </MoreInfo>
      <div
        v-if="created"
        class="extension-token"
        data-test="agenda-url"
      >
        <code>{{ created }}</code>
        <button
          type="button"
          class="link"
          @click="copy"
        >
          {{ copied ? "Copié" : "Copier l'adresse" }}
        </button>
        <p class="hint">
          Montrée une seule fois : colle-la maintenant dans ton agenda.
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
          <span>{{ token.name }} <span class="muted">· relu {{ day(token.last_used_at) }}</span></span>
          <button
            type="button"
            class="link danger"
            data-test="agenda-revoke"
            @click="revoke(token)"
          >
            Révoquer
          </button>
        </li>
      </ul>
      <p
        v-if="createError"
        class="notice error"
        role="alert"
        data-test="agenda-error"
      >
        {{ createError }}
      </p>
      <div class="form-actions">
        <button
          type="button"
          class="secondary small"
          :disabled="creating"
          data-test="agenda-create"
          @click="create"
        >
          Créer une adresse d'abonnement
        </button>
      </div>
    </fieldset>
  </div>
</template>
