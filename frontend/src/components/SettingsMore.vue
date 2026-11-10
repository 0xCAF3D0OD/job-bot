<script setup lang="ts">
import { computed, onMounted } from "vue";

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
const rubric = (id: string) => ({ path: "/reglages", query: { rubrique: id } });

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
        :to="rubric('recherche')"
        data-test="account-orp"
      />
      <BlockRow
        title="Rythme"
        :to="rubric('rythme')"
        data-test="account-rhythm"
      />
      <BlockRow
        title="IA"
        :to="rubric('ia')"
        data-test="account-ai"
      />
      <BlockRow
        title="Agenda"
        :to="rubric('outils')"
        data-test="account-tools"
      />
      <BlockRow
        title="Formule"
        :lines="[planName]"
        :to="rubric('formule')"
        data-test="account-plan"
      />
      <BlockRow
        v-if="owner"
        title="Administration"
        :to="rubric('plateforme')"
        data-test="account-admin"
      />
      <!-- La démo ne collecte rien (docs/72). -->
      <BlockRow
        v-if="me && !me.demo"
        title="Collecter maintenant"
        :lines="[running ? 'Relève en cours…' : 'Relever tout de suite les offres des sites suivis']"
        :aria-busy="running || undefined"
        :aria-disabled="running || undefined"
        data-test="account-collect"
        @click="running || collectNow()"
      />
      <BlockRow
        v-if="showDiagnostic"
        title="État du service"
        to="/reglages/diagnostic"
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
/* Une carte de groupe comme Compte : trait de 1,5 px, lignes séparées par un filet de 1 px (--row-sep). */
/* Sur une rubrique seule (821 à 1 023 px), le titre reste visible : ce n'est pas le titre de la page. */
.settings-sub #plus > .section-title { display: block; }
.settings-more-group { overflow: hidden; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.settings-more-group > .block-row { margin: 0; border: 0; border-radius: 0; background: transparent; }
.settings-more-group > .block-row + .block-row { border-top: 1px solid var(--row-sep); }
</style>
