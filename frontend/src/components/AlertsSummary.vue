<script setup lang="ts">
import { computed } from "vue";

import type { AlertsPage } from "../api/client";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";

// Résumé des alertes (docs/21 §4) : une ligne par recherche, l'aide seulement si besoin.
// Mise en page 0.84.3 : en tête le nombre et « Gérer mes alertes » ; chaque recherche sur sa
// ligne, séparée par un filet, les mots et le lieu à gauche, l'état en pastille à droite.
const props = defineProps<{ page: AlertsPage }>();
const emit = defineEmits<{ manage: []; restart: [] }>();

// Rien reçu 24 heures après la création : l'aide (docs/121 §B.3).
const WAIT_HOURS = 24;
const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

type Cell = AlertsPage["searches"][number]["cells"][number];
const late = (cell: Cell): boolean =>
  cell.status === "created" && !!cell.created_at && Date.now() - Date.parse(cell.created_at) > WAIT_HOURS * 3_600_000;

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
// Sites dont une alerte créée n'a rien envoyé depuis 24 heures : l'aide.
const lateSites = computed(() => {
  const slugs = new Set(rows.value.flatMap((r) => r.waiting.map((c) => c.site)));
  return props.page.sites.filter((s) => slugs.has(s.slug));
});
const lateDetail = computed(() => {
  const box = props.page.mailbox ? `${props.page.mailbox}${props.page.folder ? `, dossier ${props.page.folder}` : ""}` : "la boîte lue par la plateforme";
  const senders = lateSites.value.flatMap((s) => s.senders).join(", ");
  return `Ses e-mails doivent arriver dans ${box}${senders ? ` (expéditeurs : ${senders})` : ""}.`;
});
const STATES: Record<string, string> = {
  ok: "Reçue",
  late: "Rien reçu depuis 24 heures",
  pending: "En attente du premier envoi",
  todo: "À créer",
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
      <div class="summary-title">
        <strong>{{ plural(activeCount, "recherche suivie", "recherches suivies") }}</strong>
        <span
          v-if="lastReceived"
          class="hint"
        >Dernière alerte reçue le {{ dateFormat.format(new Date(lastReceived)) }}</span>
      </div>
      <button
        type="button"
        class="pill"
        data-test="manage-alerts"
        @click="emit('manage')"
      >
        <span class="with-icon"><AppIcon name="settings" />Gérer mes alertes</span>
      </button>
    </div>
    <ul class="summary-list">
      <li
        v-for="row in rows"
        :key="row.search.id"
        :class="row.state"
        data-test="summary-row"
      >
        <span class="summary-search">
          <strong>{{ row.search.terms }}</strong>
          <span class="hint">{{ row.search.location || "Toute la Suisse" }}</span>
        </span>
        <span class="summary-state">
          <span
            class="dot"
            aria-hidden="true"
          />
          {{ STATES[row.state] }}<template v-if="row.received.length"> · {{ siteNames(row.received) }}</template>
        </span>
      </li>
    </ul>
    <!-- Une ligne, avec quoi faire (docs/interface.md, titres et textes 5) ; le détail (boîte,
         expéditeurs) au survol. -->
    <p
      v-if="lateSites.length"
      class="notice"
      data-test="late-help"
    >
      <HoverNote :text="lateDetail">
        Rien reçu de {{ lateSites.map((s) => s.name).join(", ") }} depuis 24 heures : vérifie l'alerte sur le site.
      </HoverNote>
    </p>
    <button
      type="button"
      class="link summary-add"
      data-test="restart-wizard"
      @click="emit('restart')"
    >
      <span class="with-icon"><AppIcon name="plus" />Ajouter des alertes avec l'assistant</span>
    </button>
  </section>
</template>
