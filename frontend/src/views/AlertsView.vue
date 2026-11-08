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
import FaceTransform from "../components/FaceTransform.vue";
import FirstOffers from "../components/FirstOffers.vue";
import FormField from "../components/FormField.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import ReceivedAlerts from "../components/ReceivedAlerts.vue";
import SidePanel from "../components/SidePanel.vue";
import SiteMail from "../components/SiteMail.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import StatusPill from "../components/StatusPill.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { offerUndo } from "../composables/useUndo";
import { dateInSentence } from "../dates";
import type { SiteState } from "../alertsState";
import { plural } from "../format";

// Onglet Alertes (planche « 6. Alertes », 1.6.70, structure inspirée des pages des CFF) : la
// conclusion, une seule bande d'action (§3), puis « Mes recherches » (une carte par recherche, une
// ligne par site), les messages des sites et les alertes reçues, chacun en trois lignes avec « Tout
// voir » (divulgation progressive). L'assistant reste l'entrée tant que rien n'est en place.
const page = ref<AlertsPage | null>(null);
// Ordinateur dès 1 024 px (maquette du 8 novembre, AlertesOrdinateur) : une page à elle, sur 880 px. Le titre « Mes
// alertes e-mail », la phrase et « + Ajouter une recherche » ; la bande en bandeau pêche ; « Recherches suivies » en
// une liste, une ligne par recherche et par site (les mots, les lieux · le site, l'état, « … »).
const { phone } = usePhone();
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const wide = computed(() => wideQuery.value && !phone.value);
// Téléphone (maquette du 8 novembre, AlertesTel) : une page à elle aussi, avec le retour aux candidatures, le titre
// « Alertes e-mail », la phrase, le bandeau pêche et la même liste qu'à l'ordinateur ; « + Ajouter » à côté de
// « Recherches suivies ».
const listed = computed(() => wide.value || phone.value);
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

// La phrase sous le titre, sur ordinateur : « 5 recherches suivies. Dernière alerte reçue le 7 novembre. »
const deskSentence = computed(() => {
  if (!page.value) return "";
  const { active, lastReceived } = alertsDigest(page.value);
  if (!active) return "Aucune recherche suivie pour l'instant.";
  const count = `${plural(active, "recherche", "recherches")} ${active > 1 ? "suivies" : "suivie"}.`;
  return `${count} ${lastReceived ? `Dernière alerte reçue ${dateInSentence(lastReceived)}.` : "Aucune alerte reçue pour l'instant."}`;
});

const now = ref(new Date());
const groups = computed<SearchGroup[]>(() => (page.value ? searchGroups(page.value, now.value) : []));
const band = computed(() => (page.value ? alertsBand(page.value, now.value) : null));
// Les lignes de la liste sur ordinateur : une par recherche et par site.
const SITE_TONE: Record<SiteState["kind"], "neutral" | "todo" | "ok"> = { received: "ok", quiet: "neutral", waiting: "neutral", silent: "todo", todo: "todo" };
const rows = computed(() =>
  groups.value.flatMap((group) =>
    group.sites.map((site) => ({
      key: `${group.terms}-${site.slug}`,
      group,
      site,
      place: `${group.locations.join(", ") || "Toute la Suisse"} · ${site.name}`,
    })),
  ),
);
function rowMenu(group: SearchGroup): MoreMenuItem[] {
  return [
    { label: "Modifier la recherche", test: "search-manage", icon: "pencil", run: () => (mode.value = "manage") },
    { label: "Supprimer la recherche", test: "search-remove", icon: "trash", danger: true, run: () => void remove(group) },
  ];
}

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
const addFailed = ref(false);
async function add(): Promise<void> {
  addError.value = "";
  addFailed.value = false;
  if (!form.value.terms.trim()) {
    addError.value = "Indique au moins un mot.";
    document.querySelector<HTMLInputElement>("[data-test=add-search-terms]")?.focus();
    return;
  }
  const { data } = await api.POST("/api/alert-searches", {
    body: { terms: form.value.terms.trim(), location: form.value.location.trim() || null },
  });
  if (!data) {
    addFailed.value = true;
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
  <section :class="['jobs-body', 'alerts-page', { 'alerts-wide': listed, 'alerts-phone': phone }]">
    <header
      v-if="wide && page"
      class="alerts-head-wide"
    >
      <div>
        <h1>Mes alertes e-mail</h1>
        <p data-test="alerts-sentence">
          {{ deskSentence }}
        </p>
      </div>
      <button
        v-if="view === 'summary'"
        type="button"
        class="secondary"
        data-test="add-search"
        @click="adding = true"
      >
        + Ajouter une recherche
      </button>
    </header>
    <header
      v-if="phone && page"
      class="alerts-head-phone"
    >
      <RouterLink
        to="/candidatures"
        class="icon-button icon-only"
        aria-label="Retour aux candidatures"
        data-test="alerts-back"
      >
        <AppIcon name="arrow-left" />
      </RouterLink>
      <h1>Alertes e-mail</h1>
    </header>
    <template v-if="page">
      <p
        v-if="phone && view === 'summary'"
        class="alerts-sentence-phone"
        data-test="alerts-sentence"
      >
        {{ deskSentence }}
      </p>
      <!-- La conclusion d'abord (règles §3.2), puis une seule bande d'action (§3). -->
      <div
        v-if="listed && view === 'summary' && band"
        class="alerts-banner"
        role="status"
        data-test="alerts-banner"
      >
        <AppIcon name="alert" />
        <div class="alerts-banner-text">
          <strong>{{ band.title }}</strong>
          <span>{{ band.summary }}</span>
        </div>
        <button
          type="button"
          class="alerts-tonal"
          data-test="action-band-button"
          @click="bandAction"
        >
          {{ band.action }}
        </button>
      </div>
      <p
        v-if="!listed && view === 'summary' && sentence"
        class="offers-sentence alerts-sentence"
        data-test="alerts-sentence"
      >
        <strong>{{ sentence.count }}</strong>{{ sentence.rest }}
      </p>
      <ActionBand
        v-if="!listed && view === 'summary' && band"
        :title="band.title"
        :summary="band.summary"
        :action="band.action"
        @action="bandAction"
      />

      <template v-if="view === 'wizard'">
        <!-- Rien en place, la liste est vide (docs/141 §3, Alertes) : le logo transformé « cloche » au-dessus de
             l'assistant, pas le personnage. -->
        <div
          v-if="nothingYet && !focus"
          class="face-state alerts-empty"
          data-test="alerts-empty"
        >
          <FaceTransform
            kind="alerts"
            :size="96"
          />
          <h2 class="face-state-title">
            Aucune alerte pour l’instant
          </h2>
          <p class="face-state-line">
            Trois étapes pour recevoir les nouvelles offres ici.
          </p>
        </div>
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
          v-if="listed"
          class="alerts-section alerts-list-wide"
          data-test="alert-searches"
        >
          <div class="alerts-list-head">
            <h2>Recherches suivies</h2>
            <button
              v-if="phone"
              type="button"
              class="secondary"
              data-test="add-search"
              @click="adding = true"
            >
              + Ajouter
            </button>
          </div>
          <ul class="alerts-rows">
            <li
              v-for="row in rows"
              :key="row.key"
              :class="['alerts-row', { highlighted: highlighted === row.group.terms }]"
              :data-test="`alert-row-${row.group.ids[0]}-${row.site.slug}`"
            >
              <div class="alerts-row-text">
                <strong>{{ row.group.terms }}</strong>
                <span>{{ row.place }}</span>
              </div>
              <button
                v-if="row.site.state.kind === 'todo'"
                type="button"
                class="secondary"
                :aria-label="`Créer l'alerte « ${row.group.terms} » sur ${row.site.name}`"
                :data-test="`create-${row.site.slug}`"
                @click="create(row.site.slug, row.group.terms)"
              >
                {{ phone ? "Créer" : "Créer l’alerte" }}
              </button>
              <span
                v-else-if="row.site.state.kind === 'quiet'"
                class="alert-quiet"
              >{{ row.site.state.label }}</span>
              <StatusPill
                v-else
                :tone="SITE_TONE[row.site.state.kind]"
              >
                {{ row.site.state.label }}
              </StatusPill>
              <MoreMenu
                :items="rowMenu(row.group)"
                :label="`Actions pour la recherche « ${row.group.terms} »`"
                :test-id="`search-more-${row.group.ids[0]}-${row.site.slug}`"
              />
            </li>
          </ul>
          <AlertsForward
            v-if="page.personal_address && page.mailbox"
            :address="page.mailbox"
          />
        </section>
        <section
          v-else
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
        class="add-search-form"
        data-test="add-search-form"
        novalidate
        @submit.prevent="add"
      >
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Les mots"
          :width="30"
          :error="addError"
        >
          <input
            :id="id"
            v-model="form.terms"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="add-search-terms"
            @blur="addError = form.terms.trim() ? '' : 'Indique au moins un mot.'"
            @input="addError && form.terms.trim() && (addError = '')"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Le lieu"
          optional
          :width="30"
        >
          <input
            :id="id"
            v-model="form.location"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="add-search-location"
          >
        </FormField>
        <p
          v-if="addFailed"
          class="notice error"
          role="alert"
        >
          Ajout refusé : réessaie.
        </p>
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            data-test="add-search-submit"
          >
            Ajouter la recherche
          </button>
          <button
            type="button"
            class="secondary"
            data-test="add-search-cancel"
            @click="adding = false"
          >
            Annuler
          </button>
        </div>
      </form>
    </SidePanel>
  </section>
</template>
