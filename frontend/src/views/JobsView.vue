<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import type { JobsTab } from "../router";
import AppIcon from "../components/AppIcon.vue";
import CountBadge from "../components/CountBadge.vue";
import SegmentedControl, { type SegmentOption } from "../components/SegmentedControl.vue";
import { plural } from "../format";
import { usePhone } from "../composables/usePhone";

// Rubrique Candidatures (docs/19 §2, docs/83, docs/126 §1 ; docs/139 étape 5a, C1 validé le 2026-11-02) :
// trois vues, À traiter · Envoyées · Rendez-vous, sur téléphone et sur ordinateur ; « Alertes » devient un
// lien à côté du titre. Les adresses restent (/candidatures/offres, /suivi, /alertes, /rendez-vous-orp).
// Sur téléphone (maquette Candidatures) : « Alertes » monte dans l'en-tête, à côté du titre, et les vues
// sont un contrôle segmenté ; la vue ouverte y pose ses outils (#jobs-tools : recherche, « Ajouter »).
// Ordinateur dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB) : à droite des vues, « Mes alertes
// e-mail » et le nombre de recherches suivies, puis « + Ajouter une offre », qui ouvre le dialogue d'ajout.
const route = useRoute();
const router = useRouter();
const followed = ref<number | null>(null);
const { phone } = usePhone();
const { phone: wide } = usePhone("(min-width: 1024px)");
const tab = computed<JobsTab>(() => (route.meta.tab as JobsTab | undefined) ?? "offres");
const counts = ref({ offres: 0, suivi: 0, alertes: 0, "rendez-vous": 0 });

// Le titre reste « Candidatures » (docs/88) : le segment choisi dit où l'on est.
type View = Exclude<JobsTab, "alertes">;
const TABS: { key: View; label: string; path: string; hint: string }[] = [
  { key: "offres", label: "À traiter", path: "/candidatures/offres", hint: "à traiter" },
  { key: "suivi", label: "Envoyées", path: "/candidatures/suivi", hint: "à relancer ou à compléter" },
  { key: "rendez-vous", label: "Rendez-vous", path: "/candidatures/rendez-vous-orp", hint: "" },
];
const segments = computed<SegmentOption[]>(() =>
  TABS.map((item) => ({
    value: item.key,
    label: item.label,
    to: link(item.path),
    test: `jobs-tab-${item.key}`,
    // Les maquettes (téléphone, et ordinateur dès 1 024 px) n'ont pas de nombre dans les segments.
    count: phone.value || wide.value ? undefined : badge(item.key),
    hint: `${badge(item.key)} ${item.hint}`,
  })),
);

// Le mois choisi suit d'un onglet à l'autre (Suivi et Preuves ORP).
function link(path: string) {
  return typeof route.query.mois === "string" ? { path, query: { mois: route.query.mois } } : { path };
}

function badge(key: JobsTab): number {
  return counts.value[key];
}

async function refresh(): Promise<void> {
  const [today, orp, searches] = await Promise.all([
    api.GET("/api/today"),
    api.GET("/api/orp"),
    api.GET("/api/alert-searches").catch(() => ({ data: undefined })),
  ]);
  followed.value = searches.data?.searches ? searches.data.searches.filter((search) => search.active).length : null;
  counts.value = {
    // « À traiter » : le nombre de la phrase de la liste, calculé au même endroit (docs/139, C2).
    offres: today.data?.pending ?? 0,
    // Suivi : à relancer, plus les lignes ORP à compléter (docs/22 §1).
    suivi: (today.data?.to_follow_up ?? 0) + (orp.data?.incomplete ?? 0),
    alertes: today.data?.alerts_waiting ?? 0,
    "rendez-vous": 0,
  };
}

function addOffer(): void {
  void router.push({ path: "/candidatures/offres", query: { ajouter: "1" } });
}

// Pastilles relues à chaque changement d'onglet (une offre traitée, une candidature ajoutée…).
watch(
  () => route.name,
  () => void refresh(),
);
onMounted(() => void refresh());
</script>

<template>
  <!-- Mes alertes e-mail, sur ordinateur et sur téléphone (maquette du 8 novembre, AlertesOrdinateur et AlertesTel) :
       une page à elle, sans les vues. -->
  <div
    v-if="!((wide || phone) && tab === 'alertes')"
    :class="['jobs-head', { wide: tab === 'offres' }]"
  >
    <div class="jobs-title">
      <h1>Candidatures</h1>
      <!-- Sur téléphone, le lien monte dans l'en-tête, à côté du titre (maquette Candidatures). -->
      <Teleport
        v-if="phone || !wide"
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
    <!-- Les trois vues en contrôle segmenté, sur téléphone et sur ordinateur (D4, 2026-11-03) ; sur ordinateur,
         à la largeur du texte, avec le nombre de chaque vue. -->
    <SegmentedControl
      :model-value="tab"
      :options="segments"
      label="Candidatures"
      :full="phone"
      class="jobs-segments"
    />
    <div
      v-if="wide && !phone"
      class="jobs-actions"
    >
      <RouterLink
        to="/candidatures/alertes"
        class="jobs-alerts-link"
        :aria-current="tab === 'alertes' ? 'page' : undefined"
        data-test="jobs-alerts"
      >
        <AppIcon name="mail" />Mes alertes e-mail
      </RouterLink>
      <span
        v-if="followed !== null"
        class="jobs-alerts-count"
        data-test="jobs-alerts-count"
      >{{ followed ? plural(followed, "recherche suivie", "recherches suivies") : "Aucune recherche suivie" }}</span>
      <button
        type="button"
        class="secondary jobs-add"
        data-test="manual-open"
        @click="addOffer"
      >
        <span class="with-icon"><AppIcon name="plus" />Ajouter une offre</span>
      </button>
    </div>
  </div>
  <section class="band jobs-band">
    <RouterView />
  </section>
</template>
