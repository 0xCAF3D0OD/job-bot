<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type Search } from "../api/client";
import { dateWithTime } from "../dates";
import { plural, sourceLabel } from "../format";
import JournalPanel from "./JournalPanel.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Les alertes reçues (planche « 6. Alertes », 1.6.70) : les trois dernières, le site et le nombre
// d'offres en titre, la recherche et l'heure en phrase ; « Tout voir » ouvre le journal complet, avec
// ses filtres (divulgation progressive).
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

onMounted(async () => {
  const { data } = await api.GET("/api/searches", { params: { query: { limit: LATEST, offset: 0 } } });
  items.value = data?.items ?? [];
  total.value = data?.total ?? 0;
});
</script>

<template>
  <section
    class="alerts-section"
    data-test="received-alerts"
  >
    <div class="alerts-section-head">
      <h2 class="section-title">
        Alertes reçues
      </h2>
      <button
        v-if="total > LATEST || all"
        type="button"
        class="link"
        :aria-expanded="all"
        data-test="received-all"
        @click="all = !all"
      >
        {{ all ? "Les trois dernières" : "Tout voir" }}
      </button>
    </div>
    <JournalPanel v-if="all" />
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
        Aucune alerte reçue pour l'instant.
      </p>
    </SettingCard>
  </section>
</template>
