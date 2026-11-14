<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api, type AlertsPage } from "../api/client";
import { alertsDigest } from "../alertsDigest";
import { alertsBand, searchGroups, type SearchGroup } from "../alertsState";
import AlertsPhoneList from "../components/AlertsPhoneList.vue";
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
import { useJobsMemory } from "../composables/useJobsMemory";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { offerUndo } from "../composables/useUndo";
import { dateInSentence } from "../dates";
import { plural } from "../format";

// Onglet Alertes (planche « 6. Alertes », 1.6.70, structure inspirée des pages des CFF) : la
// conclusion, une seule bande d'action (§3), puis « Mes recherches » (une carte par recherche, une
// ligne par site), les messages des sites et les alertes reçues, chacun en trois lignes avec « Tout
// voir » (divulgation progressive). L'assistant reste l'entrée tant que rien n'est en place.
const { last: lastJobsPage } = useJobsMemory();
const page = ref<AlertsPage | null>(null);
// Ordinateur (maquette AlertesOrdinateur du 9 novembre, §2.8) : une page à elle, sur 880 px, à toutes les largeurs
// au-dessus du téléphone. Le retour à Candidatures, le titre « Mes alertes e-mail », la phrase et « + Ajouter une
// recherche » ; puis les familles (À confirmer, Actives, À créer), une carte par alerte. Plus de bandeau.
// Téléphone (maquette du 8 novembre, AlertesTel) : le retour aux candidatures, le titre « Alertes e-mail », la phrase,
// le bandeau pêche et la même liste.
const { phone } = usePhone();
usePageReady("alerts", () => !!page.value);
const mode = ref<"auto" | "wizard" | "manage">("auto");
// « Créer » sur une ligne : le pas à pas de ce site, pour cette recherche.
const focus = ref<{ site: string; terms: string } | null>(null);

// Rien de créé ni reçu : on commence par l'assistant.
const nothingYet = computed(
  () => !!page.value && page.value.searches.every((s) => !s.active || s.cells.every((c) => c.status === "todo")),
);
const view = computed(() => (mode.value !== "auto" ? mode.value : nothingYet.value ? "wizard" : "summary"));
// Ordinateur, rien en place et l’assistant ouvert sans site choisi : l’en-tête de AlertesOrdinateurVide.
const deskEmpty = computed(() => !phone.value && view.value === "wizard" && nothingYet.value && !focus.value);

async function load(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches");
  if (data) page.value = data;
}

async function backToSummary(): Promise<void> {
  mode.value = "auto";
  focus.value = null;
  await load();
}

// Ordinateur (planche AlertesOrdinateurSite, paquet du 13 novembre) : le panneau « Alerte <site> » s'ouvre à droite,
// au-dessus de la page, qui ne change pas ; le téléphone garde le pas à pas en pleine page.
const deskFocus = ref<{ site: string; terms: string } | null>(null);
function create(site: string, terms: string): void {
  if (!phone.value) {
    deskFocus.value = { site, terms };
    return;
  }
  focus.value = { site, terms };
  mode.value = "wizard";
}
async function deskDone(): Promise<void> {
  const from = deskFocus.value;
  deskFocus.value = null;
  await load();
  // Après le dernier site, la carte d'où l'on venait a pu changer de famille (« À créer » → « Actives ») et le
  // focus, rendu à un élément retiré, retombe sur la page : on le pose sur la carte de ce site, là où elle est.
  await nextTick();
  if (!from || (document.activeElement && document.activeElement !== document.body)) return;
  const id = page.value?.searches.find((s) => s.terms === from.terms)?.id;
  document.querySelector<HTMLElement>(`[data-test="alert-card-${id}-${from.site}"]`)?.focus();
}

// Un site demande de confirmer l'alerte (docs/65 §3) : la personne ouvre le lien elle-même.
async function confirmed(searchId: number): Promise<void> {
  const { data } = await api.POST("/api/alert-searches/confirmations/{search_id}", {
    params: { path: { search_id: searchId } },
  });
  if (data) page.value = data;
}

// La phrase sous le titre, sur ordinateur : « 5 recherches suivies. Dernière alerte reçue le 7 novembre. »
const deskSentence = computed(() => {
  if (!page.value) return "";
  const { active, lastReceived } = alertsDigest(page.value);
  if (!active) return "Aucune recherche suivie pour l’instant.";
  const count = `${plural(active, "recherche", "recherches")} ${active > 1 ? "suivies" : "suivie"}.`;
  return `${count} ${lastReceived ? `Dernière alerte reçue ${dateInSentence(lastReceived)}.` : "Aucune alerte reçue pour l’instant."}`;
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
    // Téléphone (§10.8) : le même message qu'« Offre écartée » (§10.1).
    message: phone.value ? "Recherche retirée." : `« ${group.terms} » n’est plus suivie.`,
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
  const card = document.querySelector<HTMLElement>(`[data-test^="alert-card-${group.ids[0]}-"]`);
  card?.scrollIntoView?.({ behavior: "smooth", block: "center" });
}

onMounted(async () => {
  await load();
  await arrive();
});
</script>

<template>
  <section :class="['jobs-body', 'alerts-page', 'alerts-wide', { 'alerts-phone': phone }]">
    <!-- Ordinateur (lot 11.4) : le retour à la liste de Candidatures, sur l'onglet qui était ouvert. -->
    <RouterLink
      v-if="!phone && page"
      :to="lastJobsPage"
      class="alerts-back-wide"
      data-test="alerts-back-wide"
    >
      <AppIcon name="chevron-left" />Candidatures
    </RouterLink>
    <header
      v-if="!phone && page"
      :class="['alerts-head-wide', { 'alerts-head-empty': deskEmpty }]"
    >
      <!-- Rien en place (AlertesOrdinateurVide, corrections du 13.11 au soir, §2) : Orange, 112 px de haut, à gauche
           du titre ; la phrase dit qu’il n’y a encore aucune alerte. Plus d’illustration de l’ancienne série. -->
      <img
        v-if="deskEmpty"
        class="alerts-head-orange"
        src="/illustrations/orange-salut-112.webp"
        srcset="/illustrations/orange-salut-112.webp 1x, /illustrations/orange-salut-224.webp 2x"
        width="88"
        height="112"
        alt=""
        aria-hidden="true"
        decoding="async"
        data-test="alerts-orange"
      >
      <div>
        <h1>Mes alertes e-mail</h1>
        <p data-test="alerts-sentence">
          {{ deskEmpty ? "Aucune alerte pour l’instant. Crée-les une fois, les offres arrivent ensuite ici toutes seules." : deskSentence }}
        </p>
      </div>
      <button
        v-if="view === 'summary'"
        type="button"
        class="secondary action-2"
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
      <!-- Téléphone : une seule bande d'action (§3) ; la confirmation passe par la famille « À confirmer ». -->
      <div
        v-if="phone && view === 'summary' && band && band.kind !== 'confirm'"
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
      <template v-if="view === 'wizard'">
        <!-- Rien en place, la liste est vide (docs/141 §3, Alertes) : sur téléphone, le logo transformé « cloche »
             au-dessus de l’assistant ; sur ordinateur, Orange est dans l’en-tête (corrections du 13.11, §2). -->
        <div
          v-if="phone && nothingYet && !focus"
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
          :desk="!phone"
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
        <!-- Téléphone (§10.8, 9 novembre) : les recherches rangées par famille, une carte par site, la feuille « Alerte ». -->
        <!-- Ordinateur (§2.8, AlertesOrdinateur du 9 novembre) : la même liste par famille, en cartes ; la feuille
             « Alerte » devient le panneau de droite. -->
        <AlertsPhoneList
          :page="page"
          :groups="groups"
          :desk="!phone"
          :highlighted="highlighted"
          @add="adding = true"
          @create="create"
          @remove="remove"
          @confirmed="confirmed"
        />
        <AlertsForward
          v-if="page.personal_address && page.mailbox"
          :address="page.mailbox"
        />
        <SiteMail
          :codes="page.codes ?? []"
          :guest-mailbox="!!(page.personal_address && page.guest_mailbox)"
          @refresh="load()"
        />
        <ReceivedAlerts />
        <FirstOffers where="alerts" />
      </template>
      <AlertsWizard
        v-if="!phone && deskFocus"
        :key="`${deskFocus.terms}-${deskFocus.site}`"
        :page="page"
        :focus="deskFocus"
        desk
        @updated="page = $event"
        @done="deskDone"
      />
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
