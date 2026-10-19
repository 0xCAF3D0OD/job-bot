<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import type { IconName } from "../icons";
import type { JobsTab } from "../router";

// Rubrique Candidatures (docs/19 §2, docs/42, docs/83) : cinq onglets toujours visibles sous le titre.
const route = useRoute();
const tab = computed<JobsTab>(() => (route.meta.tab as JobsTab | undefined) ?? "offres");
const counts = ref({ offres: 0, suivi: 0, alertes: 0, bilan: 0, "rendez-vous": 0 });

// Le titre reste « Candidatures » (docs/88) : l'onglet souligné dit où l'on est.
// `tabShort` : l'onglet sur téléphone, quand son nom ne tient pas avec les autres.
const TABS: {
  key: JobsTab;
  label: string;
  icon: IconName;
  tabShort?: string;
  path: string;
  hint: string;
}[] = [
  { key: "offres", label: "Offres", icon: "briefcase", path: "/candidatures/offres", hint: "à examiner" },
  {
    key: "suivi",
    label: "Suivi",
    icon: "list-check",
    path: "/candidatures/suivi",
    hint: "à relancer ou à compléter",
  },
  {
    key: "alertes",
    label: "Alertes",
    icon: "bell",
    path: "/candidatures/alertes",
    hint: "alertes créées sans rien envoyé",
  },
  {
    key: "bilan",
    label: "Bilan",
    icon: "stats",
    path: "/candidatures/bilan",
    hint: "",
  },
  {
    key: "rendez-vous",
    label: "Rendez-vous",
    icon: "calendar",
    tabShort: "RDV",
    path: "/candidatures/rendez-vous-orp",
    hint: "",
  },
];

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
    bilan: 0,
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
  <div class="jobs-head">
    <h1>Candidatures</h1>
    <nav
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
        <span class="with-icon">
          <AppIcon :name="item.icon" />
          <span
            v-if="item.tabShort"
            class="label-long"
          >{{ item.label }}</span>
          <span
            v-if="item.tabShort"
            class="label-short"
            :aria-label="item.label"
          >{{ item.tabShort }}</span>
          {{ item.tabShort ? "" : item.label }}
        </span>{{ " " }}<span
          v-if="badge(item.key)"
          class="tab-count"
          :title="`${badge(item.key)} ${item.hint}`"
        >{{ badge(item.key) }}</span>
      </RouterLink>
    </nav>
  </div>
  <section class="band jobs-band">
    <RouterView />
  </section>
</template>
