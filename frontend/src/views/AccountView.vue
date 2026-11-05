<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import GroupedList from "../components/GroupedList.vue";
import GroupedRow from "../components/GroupedRow.vue";
import PageHero from "../components/PageHero.vue";
import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { usePlan } from "../composables/usePlan";
import { useProfiles } from "../composables/useProfiles";
import { useTheme } from "../composables/useTheme";

// La page Compte (maquette Compte, docs/139 étape 10a ; décisions de Kevin du 2026-11-05) : le sommaire de tout ce
// qui te concerne, sur téléphone comme sur ordinateur. La carte du profil, puis Mon parcours, Préférences,
// Recherche et outils (absent de la maquette, C8), Confidentialité et aide. Chaque ligne ouvre sa page ou sa
// rubrique des Réglages.
const { me } = useAuth();
const { theme } = useTheme();
const { plan } = usePlan();
const { list, current, load, choose } = useProfiles();
const { running, message: collectMessage, collectNow } = useCollect();

const name = ref("");
const cvCount = ref<number | null>(null);
const operatorContact = ref<string | null>(null);

const initials = computed(() =>
  name.value
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join(""),
);
const THEME_LABEL = { auto: "Automatique", light: "Clair", dark: "Sombre" } as const;
const owner = computed(() => Boolean(me.value?.is_owner));
const planName = computed(() => (plan.value?.plan === "plus" ? "Plus" : "Essentiel"));
// Le Diagnostic technique, à l'exploitant seulement (docs/108 §3), jamais dans la démo.
const showDiagnostic = computed(() => owner.value || (me.value?.auth_enabled === false && !me.value?.demo));
// « Aide et contact » : l'e-mail de l'exploitant s'il en a donné un, sinon la page À propos qui montre son contact.
const operatorEmail = computed(() => operatorContact.value?.match(/[\w.+-]+@[\w-]+\.[\w.-]+/)?.[0] ?? null);

const rubric = (id: string) => ({ path: "/reglages", query: { rubrique: id } });

async function loadName(): Promise<void> {
  try {
    const { data } = await api.GET("/api/identity");
    name.value = data?.name?.trim() ?? "";
  } catch {
    name.value = "";
  }
}

// « Mes CV » compte les CV seulement, pas les certificats de travail (C5).
async function loadCvCount(): Promise<void> {
  try {
    const { data } = await api.GET("/api/documents");
    cvCount.value = data ? data.filter((doc) => doc.kind !== "certificate").length : null;
  } catch {
    cvCount.value = null;
  }
}

async function loadContact(): Promise<void> {
  try {
    const { data } = await api.GET("/api/privacy");
    operatorContact.value = data?.contact ?? null;
  } catch {
    operatorContact.value = null;
  }
}

function onProfileChange(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}

onMounted(() => {
  void loadName();
  void loadCvCount();
  void loadContact();
  void load();
});
</script>

<template>
  <PageHero title="Compte" />
  <section class="band">
    <div
      class="container account-page"
      data-test="account-page"
    >
      <RouterLink
        to="/profil"
        class="account-card"
        data-test="account-profile-card"
      >
        <span
          class="account-avatar"
          aria-hidden="true"
        >
          <template v-if="initials">{{ initials }}</template>
          <AppIcon
            v-else
            name="user"
          />
        </span>
        <span class="account-card-text">
          <strong class="account-card-name">{{ name || "Ton profil" }}</strong>
          <span class="account-card-line">CV, compétences, postes recherchés</span>
        </span>
        <AppIcon
          name="chevron"
          class="grouped-chevron"
        />
      </RouterLink>

      <!-- Les profils d'essai de l'exploitant (docs/65), venus du menu du compte (C2) : seulement s'il y en a. -->
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

      <GroupedList title="Mon parcours">
        <GroupedRow
          title="Formations"
          icon="book"
          to="/bilan/formations"
          data-test="account-trainings"
        />
        <GroupedRow
          title="Mes CV"
          icon="file"
          :value="cvCount === null ? '' : String(cvCount)"
          :to="{ path: '/profil', query: { onglet: 'parcours' } }"
          data-test="account-cv"
        />
      </GroupedList>

      <GroupedList title="Préférences">
        <GroupedRow
          title="Critères de recherche"
          to="/profil"
          data-test="account-criteria"
        />
        <GroupedRow
          title="Notifications"
          :to="rubric('notifications')"
          data-test="account-notifications"
        />
        <GroupedRow
          title="Apparence"
          :value="THEME_LABEL[theme]"
          :to="rubric('affichage')"
          data-test="account-appearance"
        />
      </GroupedList>

      <GroupedList title="Recherche et outils">
        <GroupedRow
          title="Objectif ORP et sites"
          :to="rubric('recherche')"
          data-test="account-orp"
        />
        <GroupedRow
          title="Rythme"
          :to="rubric('rythme')"
          data-test="account-rhythm"
        />
        <GroupedRow
          title="IA"
          :to="rubric('ia')"
          data-test="account-ai"
        />
        <GroupedRow
          title="Agenda et extension"
          :to="rubric('outils')"
          data-test="account-tools"
        />
        <GroupedRow
          title="Formule"
          :value="planName"
          :to="rubric('formule')"
          data-test="account-plan"
        />
        <GroupedRow
          v-if="owner"
          title="Administration"
          :to="rubric('plateforme')"
          data-test="account-admin"
        />
        <!-- Venu du menu du compte (C2). La démo ne collecte rien (docs/72). -->
        <GroupedRow
          v-if="me && !me.demo"
          title="Collecter maintenant"
          :description="running ? 'Relève en cours…' : 'Relever tout de suite les offres des sites suivis'"
          button
          :busy="running"
          :chevron="false"
          data-test="account-collect"
          @click="collectNow()"
        />
      </GroupedList>
      <!-- L'état de la collecte, dit aux lecteurs d'écran ; la ligne le montre à l'écran. -->
      <p
        v-if="me && !me.demo"
        class="visually-hidden"
        role="status"
        data-test="account-collect-status"
      >
        {{ running ? "Relève en cours…" : collectMessage }}
      </p>

      <GroupedList title="Confidentialité et aide">
        <GroupedRow
          title="Mes données"
          :to="rubric('donnees')"
          data-test="account-data"
        />
        <GroupedRow
          title="Ce qui part à l'IA"
          :to="{ path: '/tes-donnees', hash: '#ia' }"
          data-test="account-ai-data"
        />
        <GroupedRow
          v-if="operatorEmail"
          title="Aide et contact"
          :href="`mailto:${operatorEmail}`"
          :chevron="false"
          data-test="account-help"
        >
          <template #end>
            <AppIcon
              name="external"
              class="grouped-chevron"
            />
          </template>
        </GroupedRow>
        <GroupedRow
          v-else
          title="Aide et contact"
          to="/a-propos"
          data-test="account-help"
        />
        <GroupedRow
          v-if="showDiagnostic"
          title="État du service"
          to="/reglages/diagnostic"
          data-test="account-diagnostic"
        />
      </GroupedList>
    </div>
  </section>
</template>
