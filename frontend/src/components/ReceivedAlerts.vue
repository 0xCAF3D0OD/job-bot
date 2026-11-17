<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";

import { api, type Search } from "../api/client";
import { dateWithTime } from "../dates";
import { plural, sourceLabel } from "../format";
import JournalPanel from "./JournalPanel.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import ShowMore from "./ShowMore.vue";

// Les alertes reçues (planche « 6. Alertes », 1.6.70) : les trois dernières, le site et le nombre
// d'offres en titre, la recherche et l'heure en phrase ; « Afficher plus », en bas, déplie sur place le
// journal complet, avec ses filtres (divulgation progressive ; règles §4, ShowMore). Ouvert, le journal porte le seul
// bouton du bas : jamais deux « Afficher plus / moins » l'un sous l'autre (K20, audit du 17.11).
const LATEST = 3;
const items = ref<Search[]>([]);
const total = ref(0);
const all = ref(false);

function title(item: Search): string {
  const site = sourceLabel[item.source] ?? item.source;
  return item.results_count === null || item.results_count === undefined ? site : `${site} · ${plural(item.results_count, "offre", "offres")}`;
}
function line(item: Search): string {
  const what = item.alert_label ? `Recherche « ${item.alert_label} »` : item.subject || "Sans sujet";
  return `${what} · ${dateWithTime(item.received_at)}`;
}

// Replié depuis le journal, le focus revient sur « Afficher plus » (le bouton du journal disparaît avec lui).
const section = ref<HTMLElement | null>(null);
async function collapse(): Promise<void> {
  all.value = false;
  await nextTick();
  section.value?.querySelector<HTMLElement>("[data-test=received-all]")?.focus();
}

onMounted(async () => {
  const { data } = await api.GET("/api/searches", { params: { query: { limit: LATEST, offset: 0 } } });
  items.value = data?.items ?? [];
  total.value = data?.total ?? 0;
});
</script>

<template>
  <section
    ref="section"
    class="alerts-section"
    data-test="received-alerts"
  >
    <div class="alerts-section-head">
      <h2 class="section-title">
        Alertes reçues
      </h2>
    </div>
    <JournalPanel
      v-if="all"
      @collapse="collapse"
    />
    <SettingCard v-else>
      <SettingRow
        v-for="item in items"
        :key="item.id"
        :title="title(item)"
        :description="line(item)"
        data-test="received-alert"
      />
      <p
        v-if="!items.length"
        class="setting-row-message muted"
      >
        Aucune alerte reçue pour l’instant.
      </p>
    </SettingCard>
    <ShowMore
      v-if="total > LATEST && !all"
      v-model="all"
      :hidden="Math.max(total - LATEST, 0)"
      test-id="received-all"
    />
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (max-width: 820px) {
.alerts-section { margin-bottom: var(--space-6); }
}
</style>
