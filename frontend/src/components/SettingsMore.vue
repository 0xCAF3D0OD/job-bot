<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import BlockRow from "./BlockRow.vue";
import SettingsSection from "./SettingsSection.vue";
import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { usePlan } from "../composables/usePlan";
import { useProfiles } from "../composables/useProfiles";

// Prompt du 10 novembre (PR 20, point 1) : sur ordinateur, plus de page Compte ; l'avatar ouvre le panneau « Mon
// compte ». Les lignes de l'ancienne page qui n'ont pas de place dans ce panneau ni dans ReglagesOrdinateur
// (« Recherche et outils », absent des maquettes, C8) restent ici, sous les Réglages, pour ne perdre aucune fonction.
const { me } = useAuth();
const { plan } = usePlan();
const { list, current, load, choose } = useProfiles();
const { running, message: collectMessage, collectNow } = useCollect();

const owner = computed(() => Boolean(me.value?.is_owner));
const planName = computed(() => (plan.value?.plan === "plus" ? "Plus" : "Essentiel"));
const showDiagnostic = computed(() => owner.value || (me.value?.auth_enabled === false && !me.value?.demo));
const router = useRouter();
// Des boutons, pas des liens : RouterLink marquerait chaque ligne « page en cours » (même chemin, /reglages).
const go = (id: string) => void router.push({ path: "/reglages", query: { rubrique: id } });

function onProfileChange(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}
onMounted(() => {
  if (!list.value) void load();
});
</script>

<template>
  <SettingsSection
    id="plus"
    title="Recherche et outils"
    cards
  >
    <div class="settings-more-group">
      <BlockRow
        title="Objectif ORP et sites"
        icon="flag"
        data-test="account-orp"
        @click="go('recherche')"
      />
      <BlockRow
        title="Rythme"
        icon="clock"
        data-test="account-rhythm"
        @click="go('rythme')"
      />
      <BlockRow
        title="IA"
        icon="ai"
        data-test="account-ai"
        @click="go('ia')"
      />
      <BlockRow
        title="Agenda"
        icon="calendar"
        data-test="account-tools"
        @click="go('outils')"
      />
      <BlockRow
        title="Formule"
        :lines="[planName]"
        icon="tag"
        data-test="account-plan"
        @click="go('formule')"
      />
      <BlockRow
        v-if="owner"
        title="Administration"
        icon="settings"
        data-test="account-admin"
        @click="go('plateforme')"
      />
      <!-- La démo ne collecte rien (docs/72). -->
      <BlockRow
        v-if="me && !me.demo"
        title="Collecter maintenant"
        :lines="[running ? 'Relève en cours…' : 'Relever tout de suite les offres des sites suivis']"
        :aria-busy="running || undefined"
        :aria-disabled="running || undefined"
        icon="refresh"
        data-test="account-collect"
        @click="running || collectNow()"
      />
      <BlockRow
        v-if="showDiagnostic"
        title="État du service"
        to="/reglages/diagnostic"
        icon="activity"
        data-test="account-diagnostic"
      />
    </div>
    <p
      v-if="me && !me.demo"
      class="visually-hidden"
      role="status"
    >
      {{ running ? "Relève en cours…" : collectMessage }}
    </p>
    <!-- Les profils d'essai de l'exploitant (docs/65) : seulement s'il y en a. -->
    <label
      v-if="list && list.items.length > 1"
      class="account-switch"
    >
      <span>Profil affiché</span>
      <select
        class="field-compact"
        :value="current?.id"
        data-test="profile-switcher"
        @change="onProfileChange"
      >
        <option
          v-for="profile in list.items"
          :key="profile.id"
          :value="profile.id"
        >
          {{ profile.name }} {{ profile.is_main ? "(principal)" : "(essai)" }}
        </option>
      </select>
    </label>
  </SettingsSection>
</template>

<style>
/* Sur une rubrique seule (821 à 1 023 px), le titre reste visible : ce n'est pas le titre de la page. */
.settings-sub #plus > .section-title { display: block; }
/* Une carte de groupe comme Compte : trait de 1,5 px, lignes à flèche (D29) séparées par un filet de 1 px
   (--row-sep) ; 64 px de haut, 20 px de marge, le titre en gras, sa ligne en gris dessous. */
.settings-more-group { --more-row-h: 64px; overflow: hidden; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.settings-more-group > .block-row { display: flex; align-items: center; gap: var(--space-4); width: 100%; box-sizing: border-box; min-height: var(--more-row-h); margin: 0; padding: var(--space-3) var(--space-5); border: 0; border-radius: 0; background: transparent; color: var(--text); font: inherit; text-align: left; text-decoration: none; cursor: pointer; }
.settings-more-group > .block-row:hover { background: var(--band); }
.settings-more-group > .block-row + .block-row { border-top: 1px solid var(--row-sep); }
.settings-more-group .block-row-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.settings-more-group .block-row-title { font-weight: var(--weight-bold); }
.settings-more-group .block-row-line { font-size: var(--font-small); color: var(--text-secondary); }
</style>
