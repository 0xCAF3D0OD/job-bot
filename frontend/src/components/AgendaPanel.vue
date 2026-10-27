<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import MoreInfo from "./MoreInfo.vue";
import CopyLabel from "./CopyLabel.vue";
import { offerUndo } from "../composables/useUndo";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

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

// Révoqué au bout de 6 s, « Annuler » d'ici là (docs/108 §1).
async function revoke(token: Token): Promise<void> {
  const before = tokens.value;
  tokens.value = before.filter((t) => t.id !== token.id);
  await offerUndo({
    message: `« ${token.name} » révoqué : l'agenda ne recevra plus tes dates`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/agenda/tokens/{token_id}", { params: { path: { token_id: token.id } }, keepalive });
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

// « Relue le 15 oct. » : la dernière fois que l'agenda a lu l'adresse (texte seul, sans icône).
function lastRead(token: Token): string {
  if (!token.last_used_at) return "Pas encore relue par ton agenda.";
  return `Relue le ${new Date(token.last_used_at).toLocaleDateString("fr-CH", { day: "numeric", month: "short" })}.`;
}

onMounted(load);
</script>

<template>
  <!-- L'abonnement d'agenda (1.6.67, planche « 5. Réglages ») : une ligne d'en-tête avec l'action,
       puis l'adresse à copier et une ligne par adresse, dans la même carte (loi de proximité). -->
  <SettingCard
    class="sites-card"
    data-test="agenda-panel"
  >
    <SettingRow
      title="Abonnement d'agenda"
      description="Une adresse secrète que ton agenda relit tout seul pour y montrer tes dates."
    >
      <button
        type="button"
        class="secondary small"
        :disabled="creating"
        data-test="agenda-create"
        @click="create"
      >
        <span class="with-icon"><AppIcon name="plus" />Créer l'abonnement</span>
      </button>
    </SettingRow>
    <p
      v-if="createError"
      class="field-error setting-row-message"
      role="alert"
      data-test="agenda-error"
    >
      {{ createError }}
    </p>
    <SettingRow
      v-if="created"
      title="Nouvelle adresse"
      description="Montrée une seule fois : colle-la maintenant dans ton agenda."
      wide
    >
      <div
        class="extension-token"
        data-test="agenda-url"
      >
        <code>{{ created }}</code>
        <button
          type="button"
          class="link"
          @click="copy"
        >
          <CopyLabel
            :done="copied"
            label="Copier l'adresse"
          />
        </button>
      </div>
    </SettingRow>
    <SettingRow
      v-for="token in tokens"
      :key="token.id"
      :title="token.name"
      :description="lastRead(token)"
    >
      <IconButton
        icon="trash"
        :label="`Révoquer ${token.name}`"
        danger
        data-test="agenda-revoke"
        @click="revoke(token)"
      />
    </SettingRow>
  </SettingCard>
  <!-- Les étapes par agenda restent repliées sous la carte (trop longues pour une phrase). -->
  <MoreInfo label="Comment l'ajouter">
    <ul class="extension-steps">
      <li><strong>iPhone</strong> : Réglages › Calendrier › Comptes › Ajouter un compte › Autre › Ajouter un calendrier avec abonnement, puis colle l'adresse.</li>
      <li><strong>Google Agenda</strong> (ordinateur) : « Autres agendas » › + › « À partir de l'URL ».</li>
      <li><strong>Outlook</strong> : Ajouter un calendrier › « S'abonner à partir du web ».</li>
      <li>Google et Outlook lisent l'adresse depuis Internet : la plateforme doit y être joignable.</li>
    </ul>
  </MoreInfo>
</template>
