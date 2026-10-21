<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type AlertsPage } from "../api/client";
import AlertsPanel from "../components/AlertsPanel.vue";
import AppIcon from "../components/AppIcon.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import AlertsSummary from "../components/AlertsSummary.vue";
import AlertsWizard from "../components/AlertsWizard.vue";
import FirstOffers from "../components/FirstOffers.vue";
import SiteCodes from "../components/SiteCodes.vue";
import SiteMail from "../components/SiteMail.vue";
import JournalPanel from "../components/JournalPanel.vue";
import { usePageReady } from "../composables/usePageTransition";

// Onglet Alertes (docs/20 §1, docs/21 §4) : l'assistant tant que rien n'est en place,
// ensuite un résumé ; le tableau complet dans « Gérer mes alertes » ; le journal replié.
const page = ref<AlertsPage | null>(null);
usePageReady("alerts", () => !!page.value);
const mode = ref<"auto" | "wizard" | "manage">("auto");
const journalOpen = ref(false);

// Rien de créé ni reçu : on commence par l'assistant.
const nothingYet = computed(
  () => !!page.value && page.value.searches.every((s) => !s.active || s.cells.every((c) => c.status === "todo")),
);
const view = computed(() => (mode.value !== "auto" ? mode.value : nothingYet.value ? "wizard" : "summary"));

async function load(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches");
  if (data) page.value = data;
}

async function closeManage(): Promise<void> {
  mode.value = "auto";
  await load();
}

// Un site demande de confirmer l'alerte (docs/65 §3) : la personne ouvre le lien elle-même,
// puis la ligne s'en va.
async function confirmed(searchId: number): Promise<void> {
  const { data } = await api.POST("/api/alert-searches/confirmations/{search_id}", {
    params: { path: { search_id: searchId } },
  });
  if (data) page.value = data;
}

const received = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

onMounted(() => void load());
</script>

<template>
  <section class="jobs-body">
    <!-- Les codes des sites (docs/112) : en tête, le temps de les recopier. -->
    <SiteCodes
      v-if="page"
      :codes="page.codes ?? []"
    />
    <div
      v-if="page?.to_confirm?.length"
      class="notice to-confirm"
      data-test="to-confirm"
    >
      <p>
        <strong>À confirmer</strong> : {{ page.to_confirm?.length === 1 ? "un site demande" : "des sites demandent" }}
        de confirmer ton alerte avant de l'envoyer.
      </p>
      <ul>
        <li
          v-for="item in page.to_confirm"
          :key="item.search_id"
        >
          <span>{{ item.subject || item.site }} <span class="muted">· {{ received.format(new Date(item.received_at)) }}</span></span>
          <a
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="button-link small"
            data-test="confirm-link"
            @click="confirmed(item.search_id)"
          ><span class="with-icon">Confirmer<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
        </li>
      </ul>
    </div>
    <!-- Deux colonnes sur ordinateur (0.83.2) : la tâche à gauche, les e-mails des sites à
         droite ; chacune un titre puis une carte, alignés. Sur téléphone, l'une sous l'autre.
         « Gérer mes alertes » (le tableau) prend toute la largeur. -->
    <div
      v-if="page"
      :class="['alerts-columns', { wide: view === 'manage' }]"
    >
      <div class="alerts-main">
        <h2
          v-if="view !== 'manage'"
          class="section-title first"
        >
          Les alertes
        </h2>
        <AlertsWizard
          v-if="view === 'wizard'"
          :page="page"
          @updated="page = $event"
          @done="mode = 'auto'"
        />
        <template v-else-if="view === 'manage'">
          <button
            type="button"
            class="link"
            data-test="close-manage"
            @click="closeManage"
          >
            <span class="with-icon"><AppIcon name="arrow-left" />Retour au résumé</span>
          </button>
          <AlertsPanel />
        </template>
        <AlertsSummary
          v-else
          :page="page"
          @manage="mode = 'manage'"
          @restart="mode = 'wizard'"
        />
      </div>

      <aside
        class="alerts-aside"
        aria-label="Les e-mails des sites"
      >
        <SiteMail
          :codes="page.codes ?? []"
          :guest-mailbox="!!(page.personal_address && page.guest_mailbox)"
          @refresh="load()"
        />
        <FirstOffers where="alerts" />
      </aside>

      <DisclosureRow
        class="journal-toggle alerts-journal"
        title="Alertes reçues"
        value="le journal des e-mails lus"
        data-test="journal-toggle"
        @toggle="journalOpen = $event"
      >
        <JournalPanel v-if="journalOpen" />
      </DisclosureRow>
    </div>
  </section>
</template>
