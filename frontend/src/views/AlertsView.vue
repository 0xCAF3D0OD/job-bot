<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api, type AlertsPage } from "../api/client";
import { alertsDigest } from "../alertsDigest";
import { alertsBand, searchGroups, type SearchGroup } from "../alertsState";
import ActionBand from "../components/ActionBand.vue";
import AlertSearchCard from "../components/AlertSearchCard.vue";
import AlertsForward from "../components/AlertsForward.vue";
import AlertsPanel from "../components/AlertsPanel.vue";
import AlertsWizard from "../components/AlertsWizard.vue";
import AppIcon from "../components/AppIcon.vue";
import FirstOffers from "../components/FirstOffers.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import ReceivedAlerts from "../components/ReceivedAlerts.vue";
import SidePanel from "../components/SidePanel.vue";
import SiteMail from "../components/SiteMail.vue";
import { usePageReady } from "../composables/usePageTransition";
import { offerUndo } from "../composables/useUndo";
import { dateInSentence } from "../dates";
import { plural } from "../format";

// Onglet Alertes (planche « 6. Alertes », 1.6.70, structure inspirée des pages des CFF) : la
// conclusion, une seule bande d'action (§3), puis « Mes recherches » (une carte par recherche, une
// ligne par site), les messages des sites et les alertes reçues, chacun en trois lignes avec « Tout
// voir » (divulgation progressive). L'assistant reste l'entrée tant que rien n'est en place.
const page = ref<AlertsPage | null>(null);
usePageReady("alerts", () => !!page.value);
const mode = ref<"auto" | "wizard" | "manage">("auto");
// « Créer » sur une ligne : le pas à pas de ce site, pour cette recherche.
const focus = ref<{ site: string; terms: string } | null>(null);

// Rien de créé ni reçu : on commence par l'assistant.
const nothingYet = computed(
  () => !!page.value && page.value.searches.every((s) => !s.active || s.cells.every((c) => c.status === "todo")),
);
const view = computed(() => (mode.value !== "auto" ? mode.value : nothingYet.value ? "wizard" : "summary"));

async function load(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches");
  if (data) page.value = data;
}

async function backToSummary(): Promise<void> {
  mode.value = "auto";
  focus.value = null;
  await load();
}

function create(site: string, terms: string): void {
  focus.value = { site, terms };
  mode.value = "wizard";
}

// Un site demande de confirmer l'alerte (docs/65 §3) : la personne ouvre le lien elle-même.
async function confirmed(searchId: number): Promise<void> {
  const { data } = await api.POST("/api/alert-searches/confirmations/{search_id}", {
    params: { path: { search_id: searchId } },
  });
  if (data) page.value = data;
}

// La conclusion en haut (règles §3.2) : le nombre de recherches suivies, et la dernière alerte reçue.
const sentence = computed(() => {
  if (!page.value) return null;
  const { active, lastReceived } = alertsDigest(page.value);
  if (!active) return null;
  return {
    count: plural(active, "recherche", "recherches"),
    rest: ` ${active > 1 ? "suivies" : "suivie"}${lastReceived ? `, la dernière alerte reçue ${dateInSentence(lastReceived)}.` : ", aucune alerte reçue pour l'instant."}`,
  };
});

const now = ref(new Date());
const groups = computed<SearchGroup[]>(() => (page.value ? searchGroups(page.value, now.value) : []));
const band = computed(() => (page.value ? alertsBand(page.value, now.value) : null));

async function bandAction(): Promise<void> {
  const current = band.value;
  if (!current) return;
  if (current.kind === "code") {
    await nextTick();
    document.getElementById("site-messages")?.scrollIntoView({ behavior: "smooth", block: "start" });
  } else if (current.kind === "confirm") {
    window.open(current.url, "_blank", "noopener,noreferrer");
    await confirmed(current.searchId);
  } else {
    create(current.site, current.terms);
  }
}

// « + Ajouter » : une recherche, des mots et un lieu ; elle arrive « à créer » sur chaque site.
const adding = ref(false);
const form = ref({ terms: "", location: "" });
const addError = ref("");
async function add(): Promise<void> {
  addError.value = "";
  if (!form.value.terms.trim()) {
    addError.value = "Écris au moins un mot.";
    return;
  }
  const { data } = await api.POST("/api/alert-searches", {
    body: { terms: form.value.terms.trim(), location: form.value.location.trim() || null },
  });
  if (!data) {
    addError.value = "Ajout refusé : réessaie.";
    return;
  }
  page.value = data;
  adding.value = false;
  form.value = { terms: "", location: "" };
}

// Supprimer une recherche : tout de suite à l'écran, « Annuler » pendant 6 s (§4).
async function remove(group: SearchGroup): Promise<void> {
  const before = page.value;
  if (!before) return;
  page.value = { ...before, searches: before.searches.filter((s) => !group.ids.includes(s.id)) };
  await offerUndo({
    message: `« ${group.terms} » n'est plus suivie.`,
    commit: async (keepalive) => {
      let latest: AlertsPage | undefined;
      for (const id of group.ids) {
        const { data } = await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: id } }, keepalive });
        if (!data) return false;
        latest = data;
      }
      if (latest) page.value = latest;
    },
    restore: () => {
      page.value = before;
    },
  });
}

// Venu de la recherche globale (série du 27.10, point 2) : « Créer les alertes » amène à la carte de
// cette recherche (?recherche=…), « Modifier » au tableau des recherches (?gerer=1).
// Sans routeur (tests du composant seul), pas d'adresse à lire.
const route = useRoute() as ReturnType<typeof useRoute> | undefined;
const highlighted = ref<string | null>(null);
async function arrive(): Promise<void> {
  const query = route?.query ?? {};
  if (query.gerer) {
    mode.value = "manage";
    return;
  }
  const wanted = typeof query.recherche === "string" ? query.recherche.trim().toLowerCase() : "";
  const group = groups.value.find((g) => g.terms.trim().toLowerCase() === wanted);
  if (!group) return;
  highlighted.value = group.terms;
  await nextTick();
  const card = document.querySelector<HTMLElement>(`[data-test="alert-search-${group.ids[0]}"]`);
  card?.scrollIntoView?.({ behavior: "smooth", block: "center" });
}

onMounted(async () => {
  await load();
  await arrive();
});
</script>

<template>
  <section class="jobs-body alerts-page">
    <template v-if="page">
      <!-- La conclusion d'abord (règles §3.2), puis une seule bande d'action (§3). -->
      <p
        v-if="view === 'summary' && sentence"
        class="offers-sentence alerts-sentence"
        data-test="alerts-sentence"
      >
        <strong>{{ sentence.count }}</strong>{{ sentence.rest }}
      </p>
      <ActionBand
        v-if="view === 'summary' && band"
        :title="band.title"
        :summary="band.summary"
        :action="band.action"
        @action="bandAction"
      />

      <template v-if="view === 'wizard'">
        <button
          v-if="focus"
          type="button"
          class="link"
          data-test="close-wizard"
          @click="backToSummary"
        >
          <span class="with-icon"><AppIcon name="arrow-left" />Retour aux alertes</span>
        </button>
        <AlertsWizard
          :page="page"
          :focus="focus"
          @updated="page = $event"
          @done="backToSummary"
        />
      </template>
      <template v-else-if="view === 'manage'">
        <button
          type="button"
          class="link"
          data-test="close-manage"
          @click="backToSummary"
        >
          <span class="with-icon"><AppIcon name="arrow-left" />Retour aux alertes</span>
        </button>
        <AlertsPanel />
      </template>
      <template v-else>
        <section
          class="alerts-section"
          data-test="alert-searches"
        >
          <div class="alerts-section-head">
            <h2 class="section-title">
              Recherches suivies
            </h2>
            <button
              type="button"
              class="secondary"
              data-test="add-search"
              @click="adding = true"
            >
              <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
            </button>
          </div>
          <div class="setting-cards">
            <AlertSearchCard
              v-for="group in groups"
              :key="group.terms"
              :group="group"
              :class="{ highlighted: highlighted === group.terms }"
              @create="create($event, group.terms)"
              @manage="mode = 'manage'"
              @remove="remove(group)"
            />
          </div>
          <AlertsForward
            v-if="page.personal_address && page.mailbox"
            :address="page.mailbox"
          />
        </section>
        <SiteMail
          :codes="page.codes ?? []"
          :guest-mailbox="!!(page.personal_address && page.guest_mailbox)"
          @refresh="load()"
        />
        <ReceivedAlerts />
        <FirstOffers where="alerts" />
      </template>
    </template>
    <!-- Des blocs de chargement gardent la place (règles §6, 1.6.22). -->
    <LoadingBlocks
      v-else
      :heights="['3rem', '17.5rem', '3.5rem', '3.5rem']"
    />
    <SidePanel
      v-if="adding"
      open
      title="Ajouter une recherche"
      @close="adding = false"
    >
      <form
        class="manual-form"
        data-test="add-search-form"
        @submit.prevent="add"
      >
        <label>Les mots
          <input
            v-model="form.terms"
            type="text"
            placeholder="Linux"
            :aria-invalid="addError ? true : undefined"
            :aria-describedby="addError ? 'add-search-error' : undefined"
            data-test="add-search-terms"
          >
        </label>
        <label>Le lieu <span class="hint">(facultatif)</span>
          <input
            v-model="form.location"
            type="text"
            placeholder="Lausanne"
            data-test="add-search-location"
          >
        </label>
        <p
          v-if="addError"
          id="add-search-error"
          class="field-error"
          role="alert"
        >
          {{ addError }}
        </p>
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            data-test="add-search-submit"
          >
            Ajouter la recherche
          </button>
        </div>
      </form>
    </SidePanel>
  </section>
</template>
