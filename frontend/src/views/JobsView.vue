<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import type { IconName } from "../icons";
import type { JobsTab } from "../router";
import CountBadge from "../components/CountBadge.vue";
import SegmentedControl, { type SegmentOption } from "../components/SegmentedControl.vue";
import { usePhone } from "../composables/usePhone";

// Rubrique Candidatures (docs/19 §2, docs/83, docs/126 §1 ; docs/139 étape 5a, C1 validé le 2026-11-02) :
// trois vues, À traiter · Envoyées · Rendez-vous, sur téléphone et sur ordinateur ; « Alertes » devient un
// lien à côté du titre. Les adresses restent (/candidatures/offres, /suivi, /alertes, /rendez-vous-orp).
// Sur téléphone (maquette Candidatures) : « Alertes » monte dans l'en-tête, à côté du titre, et les vues
// sont un contrôle segmenté ; la vue ouverte y pose ses outils (#jobs-tools : recherche, « Ajouter »).
const route = useRoute();
const { phone } = usePhone();
const tab = computed<JobsTab>(() => (route.meta.tab as JobsTab | undefined) ?? "offres");
const counts = ref({ offres: 0, suivi: 0, alertes: 0, "rendez-vous": 0 });

// Le titre reste « Candidatures » (docs/88) : la vue soulignée dit où l'on est.
type View = Exclude<JobsTab, "alertes">;
const TABS: { key: View; label: string; icon: IconName; path: string; hint: string }[] = [
  { key: "offres", label: "À traiter", icon: "briefcase", path: "/candidatures/offres", hint: "à examiner" },
  { key: "suivi", label: "Envoyées", icon: "send", path: "/candidatures/suivi", hint: "à relancer ou à compléter" },
  { key: "rendez-vous", label: "Rendez-vous", icon: "calendar", path: "/candidatures/rendez-vous-orp", hint: "" },
];
const segments = computed<SegmentOption[]>(() =>
  TABS.map((item) => ({ value: item.key, label: item.label, to: link(item.path), test: `jobs-tab-${item.key}` })),
);

// Le mois choisi suit d'un onglet à l'autre (Suivi et Preuves ORP).
function link(path: string) {
  return typeof route.query.mois === "string" ? { path, query: { mois: route.query.mois } } : { path };
}

function badge(key: JobsTab): number {
  return counts.value[key];
}

async function refresh(): Promise<void> {
  const [today, orp] = await Promise.all([api.GET("/api/today"), api.GET("/api/orp")]);
  counts.value = {
    offres: today.data?.to_review ?? 0,
    // Suivi : à relancer, plus les lignes ORP à compléter (docs/22 §1).
    suivi: (today.data?.to_follow_up ?? 0) + (orp.data?.incomplete ?? 0),
    alertes: today.data?.alerts_waiting ?? 0,
    "rendez-vous": 0,
  };
}

// Pastilles relues à chaque changement d'onglet (une offre traitée, une candidature ajoutée…).
watch(
  () => route.name,
  () => void refresh(),
);
onMounted(() => void refresh());
</script>

<template>
  <div :class="['jobs-head', { wide: tab === 'offres' }]">
    <div class="jobs-title">
      <h1>Candidatures</h1>
      <!-- Sur téléphone, le lien monte dans l'en-tête, à côté du titre (maquette Candidatures). -->
      <Teleport
        to="#topbar-page-tools"
        :disabled="!phone"
        defer
      >
        <RouterLink
          to="/candidatures/alertes"
          class="jobs-alerts-link"
          :aria-current="tab === 'alertes' ? 'page' : undefined"
          data-test="jobs-alerts"
        >
          Alertes<CountBadge
            v-if="counts.alertes"
            class="tab-count"
            :title="`${counts.alertes} alertes créées sans rien envoyé`"
            :count="counts.alertes"
          />
        </RouterLink>
      </Teleport>
    </div>
    <!-- Les outils de la vue ouverte, au-dessus des vues (téléphone). -->
    <div
      id="jobs-tools"
      class="jobs-tools"
    />
    <SegmentedControl
      v-if="phone"
      :model-value="tab"
      :options="segments"
      label="Candidatures"
      full
      class="jobs-segments"
    />
    <nav
      v-else
      class="prep-tabs jobs-tabs"
      aria-label="Candidatures"
    >
      <RouterLink
        v-for="item in TABS"
        :key="item.key"
        :to="link(item.path)"
        :class="{ active: tab === item.key }"
        :aria-current="tab === item.key ? 'page' : undefined"
        :data-test="`jobs-tab-${item.key}`"
      >
        <!-- L'icône devant le nom (docs/101, règle 1). -->
        <span class="with-icon"><AppIcon :name="item.icon" />{{ item.label }}</span>{{ " " }}<CountBadge
          v-if="badge(item.key)"
          class="tab-count"
          :title="`${badge(item.key)} ${item.hint}`"
          :count="badge(item.key)"
        />
      </RouterLink>
    </nav>
  </div>
  <section class="band jobs-band">
    <RouterView />
  </section>
</template>
