<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type ScoringStatus } from "../api/client";
import AppIcon from "./AppIcon.vue";

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

onMounted(() => void load());
defineExpose({ load });
</script>

<template>
  <section
    v-if="status"
    class="card scoring-card"
    data-test="scoring"
  >
    <div class="scoring-head">
      <div>
        <h2>Intelligence artificielle</h2>
        <span class="detail">
          {{ status.configured ? `${status.model}, effort bas` : "Non configurée (réglage d'installation, voir le README)." }}
        </span>
      </div>
      <button
        v-if="status.configured && status.stale"
        type="button"
        class="primary small"
        :disabled="busy"
        data-test="rescore"
        @click="rescore"
      >
        Renoter {{ status.stale }} offre(s) <AppIcon name="chevron" />
      </button>
    </div>

    <p
      v-if="status.last_error"
      class="notice error"
      data-test="scoring-error"
    >
      {{ status.last_error.replace(/^ScoringUnavailable: /, "") }}
    </p>
    <p
      v-if="status.configured && !status.active_chunks"
      class="notice"
    >
      Aucun bloc de profil actif : l'IA résume les offres mais ne les note pas. Ajoute tes blocs dans la page Profil.
    </p>

    <div
      v-if="status.configured"
      class="budget"
    >
      <div class="budget-line">
        <span>Dépense du mois</span>
        <strong>{{ status.month_spend_chf }} / {{ status.budget_chf }} CHF</strong>
      </div>
      <div
        class="budget-bar"
        role="progressbar"
        :aria-valuenow="Math.round(spendRatio * 100)"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <span
          :class="{ full: status.budget_reached }"
          :style="{ width: `${spendRatio * 100}%` }"
        />
      </div>
    </div>

    <dl
      v-if="status.configured"
      class="facts"
    >
      <div><dt>Notées</dt><dd>{{ status.scored }}</dd></div>
      <div><dt>À noter</dt><dd>{{ status.unscored }}</dd></div>
      <div><dt>Lots en cours</dt><dd>{{ status.pending_batches }}</dd></div>
      <div><dt>Échecs</dt><dd>{{ status.failed }}</dd></div>
    </dl>
    <p
      v-if="status.configured && remote?.pending"
      class="remote-read"
      data-test="remote-read"
    >
      <span>Télétravail pas encore relevé sur {{ remote.pending }} offre(s) à examiner, notées avant.</span>
      <button
        type="button"
        class="link"
        :disabled="busy"
        @click="readRemote"
      >
        Relire ({{ Number(remote.estimate_usd) >= 0.01 ? `environ ${remote.estimate_usd.replace(".", ",")} $` : "moins de 0,01 $" }})
      </button>
    </p>
    <p
      v-if="message"
      role="status"
      class="muted"
    >
      {{ message }}
    </p>
  </section>
</template>
