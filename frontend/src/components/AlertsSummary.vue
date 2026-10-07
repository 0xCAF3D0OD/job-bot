<script setup lang="ts">
import { computed } from "vue";

import type { AlertsPage } from "../api/client";

// Résumé des alertes (docs/21 §4) : un point par recherche, l'aide seulement si besoin.
const props = defineProps<{ page: AlertsPage }>();
const emit = defineEmits<{ manage: []; restart: [] }>();

const WAIT_DAYS = 3;
const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

type Cell = AlertsPage["searches"][number]["cells"][number];
const late = (cell: Cell): boolean =>
  cell.status === "created" && !!cell.created_at && Date.now() - Date.parse(cell.created_at) > WAIT_DAYS * 86_400_000;

const rows = computed(() =>
  props.page.searches
    .filter((s) => s.active)
    .map((search) => {
      const received = search.cells.filter((c) => c.status === "received");
      const waiting = search.cells.filter(late);
      const lastReceived = received.map((c) => c.received_at!).sort().at(-1) ?? null;
      const state = received.length ? "ok" : waiting.length ? "late" : search.cells.some((c) => c.created_at) ? "pending" : "todo";
      return { search, received, waiting, lastReceived, state };
    }),
);
const activeCount = computed(() => rows.value.filter((r) => r.received.length || r.search.cells.some((c) => c.created_at)).length);
const lastReceived = computed(() => rows.value.map((r) => r.lastReceived).filter(Boolean).sort().at(-1) ?? null);
// Sites dont une alerte créée n'a rien envoyé depuis 3 jours : l'aide au transfert.
const lateSites = computed(() => {
  const slugs = new Set(rows.value.flatMap((r) => r.waiting.map((c) => c.site)));
  return props.page.sites.filter((s) => slugs.has(s.slug));
});
const STATES: Record<string, string> = {
  ok: "reçue",
  late: "rien reçu depuis 3 jours",
  pending: "créée, en attente du premier envoi",
  todo: "à créer",
};
const siteNames = (cells: Cell[]): string =>
  cells.map((c) => props.page.sites.find((s) => s.slug === c.site)?.name ?? c.site).join(", ");
</script>

<template>
  <section
    class="form-card alerts-summary"
    data-test="alerts-summary"
  >
    <div class="summary-head">
      <p>
        <strong>{{ activeCount }} recherche(s) suivie(s)</strong>
        <template v-if="lastReceived">
          · dernière alerte reçue le {{ dateFormat.format(new Date(lastReceived)) }}
        </template>
      </p>
      <button
        type="button"
        class="secondary small"
        data-test="manage-alerts"
        @click="emit('manage')"
      >
        Gérer mes alertes
      </button>
    </div>
    <ul class="summary-list">
      <li
        v-for="row in rows"
        :key="row.search.id"
        :class="row.state"
        data-test="summary-row"
      >
        <span
          class="dot"
          aria-hidden="true"
        />
        <span>
          <strong>{{ row.search.terms }}</strong> · {{ row.search.location || "toute la Suisse" }}
          <span class="hint">
            — {{ STATES[row.state] }}<template v-if="row.received.length"> ({{ siteNames(row.received) }})</template>
          </span>
        </span>
      </li>
    </ul>
    <div
      v-if="lateSites.length"
      class="notice"
      data-test="late-help"
    >
      Rien reçu de {{ lateSites.map((s) => s.name).join(", ") }} ? Vérifie que l'alerte est bien créée sur le site et
      que ses e-mails arrivent dans
      <template v-if="page.mailbox">
        <strong>{{ page.mailbox }}</strong>, dossier <strong>{{ page.folder }}</strong>
      </template>
      <template v-else>
        la boîte lue par la plateforme
      </template>
      (expéditeurs : {{ lateSites.flatMap((s) => s.senders).join(", ") || "voir Réglages › Sites suivis" }}).
    </div>
    <button
      type="button"
      class="link"
      data-test="restart-wizard"
      @click="emit('restart')"
    >
      Ajouter des alertes avec l'assistant
    </button>
  </section>
</template>
