<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type ScoringStatus } from "../api/client";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

const status = ref<ScoringStatus | null>(null);
// Offres déjà notées dont le télétravail n'est pas relevé (docs/26 §2).
const remote = ref<{ pending: number; estimate_usd: string } | null>(null);
const message = ref("");
const busy = ref(false);

const spendRatio = computed(() => {
  if (!status.value) return 0;
  const budget = Number(status.value.budget_chf);
  return budget > 0 ? Math.min(1, Number(status.value.month_spend_chf) / budget) : 1;
});

async function load(): Promise<void> {
  try {
    const { data } = await api.GET("/api/scoring");
    status.value = data ?? null;
    const pending = await api.GET("/api/scoring/remote");
    remote.value = pending.data ?? null;
  } catch {
    status.value = null; // API injoignable : les voyants de la page le signalent déjà
  }
}

async function rescore(): Promise<void> {
  busy.value = true;
  try {
    const { data, response } = await api.POST("/api/rescore");
    message.value =
      response.status === 409
        ? "IA non configurée."
        : data?.result === "already_queued"
          ? "Une renotation attend déjà son tour."
          : "Renotation lancée, en lot : les notes arrivent d'ici une heure environ.";
  } finally {
    busy.value = false;
  }
}

async function readRemote(): Promise<void> {
  busy.value = true;
  try {
    const { data, response } = await api.POST("/api/scoring/remote");
    message.value =
      response.status === 409
        ? "IA non configurée."
        : data?.result === "already_queued"
          ? "Une relecture attend déjà son tour."
          : "Relecture lancée : le télétravail apparaît sur les offres d'ici quelques minutes.";
  } finally {
    busy.value = false;
  }
}

// Les compteurs en une phrase (planche « 5. Réglages ») : les notées à droite, le reste dessous.
const counts = computed(() => {
  const s = status.value;
  if (!s) return "";
  return [
    `${s.unscored} à noter`,
    plural(s.pending_batches, "lot en cours", "lots en cours", "aucun lot en cours"),
    plural(s.failed, "échec", "échecs", "aucun échec"),
  ].join(" · ") + ".";
});
const remoteCost = computed(() =>
  remote.value && Number(remote.value.estimate_usd) >= 0.01
    ? `environ ${remote.value.estimate_usd.replace(".", ",")} $`
    : "moins de 0,01 $",
);

onMounted(() => void load());
defineExpose({ load });
</script>

<template>
  <!-- L'IA de la plateforme (1.6.67, planche « 5. Réglages ») : une carte de lignes, l'état écrit en
       mots à droite (WCAG 1.4.1), les actions à droite de leur ligne. -->
  <SettingCard
    v-if="status"
    data-test="scoring"
  >
    <SettingRow
      title="Intelligence artificielle"
      :description="status.configured ? 'Elle note les offres.' : 'Réglage d\'installation, voir le README.'"
    >
      <span :class="['state-word', status.configured ? 'ok' : 'warn']">{{ status.configured ? "Active" : "Non configurée" }}</span>
    </SettingRow>
    <SettingRow
      v-if="status.last_error"
      title="Dernière erreur"
      :description="status.last_error.replace(/^ScoringUnavailable: /, '')"
      data-test="scoring-error"
    >
      <span class="state-word down">À corriger</span>
    </SettingRow>
    <SettingRow
      v-if="status.configured && !status.active_chunks"
      title="Profil"
      description="Aucun bloc de profil actif : les offres ne sont pas notées. Ajoute tes blocs dans Profil."
    >
      <span class="state-word warn">Vide</span>
    </SettingRow>
    <template v-if="status.configured">
      <SettingRow
        title="Dépense du mois"
        :description="`${status.month_spend_chf} / ${status.budget_chf} CHF`"
      >
        <div
          class="budget-bar"
          role="progressbar"
          aria-label="Dépense du mois"
          :aria-valuenow="Math.round(spendRatio * 100)"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span
            :class="{ full: status.budget_reached }"
            :style="{ width: `${spendRatio * 100}%` }"
          />
        </div>
        <span>{{ Math.round(spendRatio * 100) }} %</span>
      </SettingRow>
      <SettingRow
        title="Offres notées"
        :description="counts"
        data-test="scoring-counts"
      >
        <strong>{{ status.scored }}</strong>
      </SettingRow>
      <SettingRow
        v-if="status.stale"
        title="Notes à refaire"
        :description="`${plural(status.stale, 'offre notée', 'offres notées')} avec un ancien profil.`"
      >
        <button
          type="button"
          class="secondary small"
          :disabled="busy"
          data-test="rescore"
          @click="rescore"
        >
          <span class="with-icon"><AppIcon name="ai" />Renoter</span>
        </button>
      </SettingRow>
      <SettingRow
        v-if="remote?.pending"
        title="Télétravail à relever"
        :description="`${plural(remote.pending, 'offre notée', 'offres notées')} avant, à examiner · ${remoteCost}.`"
        data-test="remote-read"
      >
        <button
          type="button"
          class="secondary small"
          :disabled="busy"
          @click="readRemote"
        >
          <span class="with-icon"><AppIcon name="ai" />Relire</span>
        </button>
      </SettingRow>
    </template>
    <p
      v-if="message"
      role="status"
      class="hint setting-row-message"
      data-test="scoring-message"
    >
      {{ message }}
    </p>
  </SettingCard>
</template>
