<script setup lang="ts">
import { computed } from "vue";

import type { AlertsPage } from "../api/client";
import { alertRows } from "../alertsDigest";
import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";

// Résumé des alertes (docs/21 §4) : une ligne par recherche, l'aide seulement si besoin.
// Mise en page 0.84.3 : en tête « Les alertes » et « Gérer mes alertes » (le nombre et la date
// passent dans la phrase de conclusion de la page, 1.6.22) ; chaque recherche sur sa ligne,
// séparée par un filet, les mots et le lieu à gauche, l'état en pastille à droite.
const props = defineProps<{ page: AlertsPage }>();
const emit = defineEmits<{ manage: []; restart: [] }>();

type Cell = AlertsPage["searches"][number]["cells"][number];
const rows = computed(() => alertRows(props.page));
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
      <h2 class="summary-title">
        Les alertes
      </h2>
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
