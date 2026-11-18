<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import type { JobsTab } from "../router";
import AppIcon from "../components/AppIcon.vue";
import CountBadge from "../components/CountBadge.vue";
import FolderTabs, { type FolderTab } from "../components/FolderTabs.vue";
import { plural } from "../format";
import { usePhone } from "../composables/usePhone";

// Rubrique Candidatures (docs/19 §2, docs/83, docs/126 §1 ; docs/139 étape 5a, C1 validé le 2026-11-02) :
// trois vues, À traiter · Envoyées · Rendez-vous, sur téléphone et sur ordinateur ; « Alertes » devient un
// lien à côté du titre. Les adresses restent (/candidatures/offres, /suivi, /alertes, /rendez-vous-orp).
// Sur téléphone (maquette Candidatures) : « Alertes » monte dans l'en-tête, à côté du titre, et les vues
// sont un contrôle segmenté ; la vue ouverte y pose ses outils (#jobs-tools : recherche, « Ajouter »).
// Ordinateur dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB) : à droite des vues, « Mes alertes
// e-mail » et le nombre de recherches suivies, puis « + Ajouter », qui ouvre le panneau d'ajout (une offre ou une candidature spontanée, §2.6 du 9 novembre).
const route = useRoute();
const router = useRouter();
const followed = ref<number | null>(null);
// L'état vide des Offres (§13 du 15 novembre) change selon qu'une recherche est suivie ou non.
provide("followedSearches", followed);
// La prochaine collecte planifiée (§41 du 16.11), pour la pastille de Candidatures vide.
const nextCollectAt = ref<string | null>(null);
provide("nextCollectAt", nextCollectAt);
const { phone } = usePhone();
const { phone: wide } = usePhone("(min-width: 1024px)");
const tab = computed<JobsTab>(() => (route.meta.tab as JobsTab | undefined) ?? "offres");
const counts = ref({ offres: 0, suivi: 0, alertes: 0, "rendez-vous": 0 });
const fresh = ref({ offres: 0, "rendez-vous": 0 });

// Le titre reste « Candidatures » (docs/88) : le segment choisi dit où l'on est.
type View = Exclude<JobsTab, "alertes">;
const TABS: { key: View; label: string; path: string; hint: string }[] = [
  { key: "offres", label: "Offres", path: "/candidatures/offres", hint: "pas encore envoyées" },
  { key: "suivi", label: "Envoyées", path: "/candidatures/suivi", hint: "à relancer ou à compléter" },
  { key: "rendez-vous", label: "Rendez-vous", path: "/candidatures/rendez-vous-orp", hint: "" },
];
// Les pastilles des onglets (§47 du 17.11, planches téléphone et ordinateur dès 1 024 px) : les nouvelles offres
// (accent) et les rendez-vous à noter (orange) ; rien à zéro, rien sur Envoyées. Entre 821 et 1 023 px, sans planche,
// les nombres d'avant restent : à traiter et à relancer.
const segments = computed<FolderTab[]>(() =>
  TABS.map((item) => {
    const planche = phone.value || wide.value;
    const count = planche ? (item.key === "suivi" ? 0 : fresh.value[item.key]) : item.key === "rendez-vous" ? 0 : badge(item.key);
    return {
      value: item.key,
      label: item.label,
      to: link(item.path),
      test: `jobs-tab-${item.key}`,
      count,
      tone: item.key === "rendez-vous" ? "orange" : "accent",
      hint: planche ? `${count} ${item.key === "rendez-vous" ? "à noter" : "nouvelles"}` : `${count} ${item.hint}`,
    };
  }),
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
  nextCollectAt.value = today.data?.next_collect_at ?? null;
  followed.value = searches.data?.searches ? searches.data.searches.filter((search) => search.active).length : null;
  counts.value = {
    // « À traiter » : le nombre de la phrase de la liste, calculé au même endroit (docs/139, C2).
    offres: today.data?.pending ?? 0,
    // Suivi : à relancer, plus les lignes ORP à compléter (docs/22 §1).
    suivi: (today.data?.to_follow_up ?? 0) + (orp.data?.incomplete ?? 0),
    alertes: today.data?.alerts_waiting ?? 0,
    "rendez-vous": 0,
  };
  // Les pastilles des planches (§47) : les offres nouvelles (statut « Nouvelles », §38) et les rendez-vous passés à noter.
  fresh.value = { offres: today.data?.to_review ?? 0, "rendez-vous": today.data?.interviews_to_review?.length ?? 0 };
}

// « + Ajouter » de l'en-tête (maquette du 14 novembre, §6) : sur Rendez-vous, le seul bouton d'ajout ; il ouvre le
// panneau « Nouveau rendez-vous » de la page. Ailleurs, l'ajout d'une offre.
function addOffer(): void {
  if (tab.value === "rendez-vous") void router.push({ path: "/candidatures/rendez-vous-orp", query: { ...route.query, ajouter: "1" } });
  else void router.push({ path: "/candidatures/offres", query: { ajouter: "1" } });
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
    :class="['jobs-head', 'jobs-candidatures', 'folder-head', { wide: tab === 'offres' }]"
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
        <!-- La place du bouton Filtres d'Offres et d'Envoyées, le temps que la vue le pose : « Alertes » ne glisse
             plus de 44 px sous le doigt (audit du 17.11, N19). Masquée dès que le bouton est là. Gardée aussi sur
             Rendez-vous, qui n'a pas de bouton Filtres : « Alertes » reste à la même place (planche RendezVous, §72). -->
        <span
          v-if="phone && (tab === 'offres' || tab === 'suivi' || tab === 'rendez-vous')"
          class="jobs-filter-slot"
          aria-hidden="true"
        />
      </Teleport>
    </div>
    <!-- Les outils de la vue ouverte, au-dessus des vues (téléphone). -->
    <!-- Sur téléphone, sa place est gardée pendant que la vue se charge : sinon les onglets montent de 60 px, puis
         redescendent quand la recherche arrive (audit du 17.11, K16). -->
    <div
      id="jobs-tools"
      :class="['jobs-tools', { 'jobs-tools-reserve': phone }]"
    />
    <!-- Les trois vues en onglets « dossier » (§47 du 17.11), sur téléphone et sur ordinateur ; sur ordinateur, à
         droite du titre, la ligne traversant tout l’en-tête. -->
    <FolderTabs
      :selected="tab"
      :tabs="segments"
      label="Candidatures"
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
        :aria-haspopup="tab === 'rendez-vous' ? 'dialog' : undefined"
        data-test="manual-open"
        @click="addOffer"
      >
        <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
      </button>
    </div>
  </div>
  <section class="band jobs-band jobs-candidatures-band">
    <RouterView />
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
/* La hauteur de la recherche (48 px) et son écart, gardés vides le temps du chargement (audit K16). */
.jobs-head .jobs-tools.jobs-tools-reserve:empty { display: block; min-height: var(--field-h); margin: 0 0 var(--space-3); }
.jobs-filter-slot { flex: none; width: var(--target-min); height: var(--target-min); }
.topbar-page-tools:has([data-test=filters-toggle], [data-test=sent-filters-toggle]) .jobs-filter-slot { display: none; }
@media (min-width: 1024px) {
/* Onglets dossier (§47 du 17.11) : la ligne traverse l'en-tête sous le titre, les onglets et les actions ; le titre
   est remonté de 8 px, « Mes alertes e-mail » et « Ajouter » de 12 px (6 et 10 sur la planche, mis sur la grille de 4). */
.jobs-head.folder-head { position: relative; }
.jobs-head.folder-head::after { content: ""; position: absolute; left: var(--space-6); right: var(--space-6); bottom: -1.5px; height: 1.5px; background: var(--tab-line); }
.jobs-head .jobs-segments { order: 2; height: auto; padding: 0; border: 0; }
.jobs-actions { order: 3; display: flex; align-items: center; gap: var(--space-2); margin: 0 0 var(--space-3) auto; }
.jobs-actions { --alerts-gap: 28px; --add-pad: 18px; }
.jobs-alerts-count { margin-right: var(--alerts-gap); font-size: var(--font-label); font-weight: var(--weight-semibold); color: var(--text-secondary); }
}
</style>
