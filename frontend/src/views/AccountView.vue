<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import AvatarPicker from "../components/AvatarPicker.vue";
import BlockRow from "../components/BlockRow.vue";
import PageHero from "../components/PageHero.vue";
import ProfileImage from "../components/ProfileImage.vue";
import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { useProfileImage } from "../composables/useProfileImage";
import { useProfiles } from "../composables/useProfiles";
import { useTheme } from "../composables/useTheme";
import { plural } from "../format";
import "../blocks.css";

// Prompt du 9 novembre, PR 8 (maquettes Compte et CompteSombre) : une carte par groupe (profil ; Mon parcours ;
// Préférences ; Confidentialité et aide ; Se déconnecter), lignes séparées par un trait fin, comme Réglages ; plus de
// trait entre les groupes, 12 px au-dessus et au-dessous de chacun.
// La page Compte (maquette Compte, docs/139 étape 10a ; décisions de Kevin du 2026-11-05) : le sommaire de tout ce
// qui te concerne, sur téléphone comme sur ordinateur. La carte du profil, puis Mon parcours, Préférences,
// Recherche et outils (absent de la maquette, C8), Confidentialité et aide. Chaque ligne ouvre sa page ou sa
// rubrique des Réglages.
const { me, logout } = useAuth();
const router = useRouter();

// « Se déconnecter » sous les blocs, en --danger (§10.4, 9 novembre) : comme le pied du panneau du compte.
async function signOut(): Promise<void> {
  await logout();
  await router.push({ name: "news" });
}
const { theme } = useTheme();
const { phone } = usePhone();
const { plan } = usePlan();
const { list, current, load, choose } = useProfiles();
const { running, message: collectMessage, collectNow } = useCollect();

const name = ref("");
const image = useProfileImage();
const picking = ref(false);
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
  void image.load();
});
</script>

<template>
  <PageHero title="Compte" />
  <section class="band blocks-page account-blocks">
    <div
      class="container account-page"
      data-test="account-page"
    >
      <!-- Maquette du 8 novembre (Compte, CompteImage) : l'image de profil avec sa pastille crayon ; un toucher ouvre
           « Ton image » (AvatarPicker). Le bouton est posé à côté du lien de la carte, pas dedans. -->
      <section class="block account-card-wrap">
        <div class="account-group account-profile-group">
          <RouterLink
            to="/profil"
            class="block-row account-card"
            data-test="account-profile-card"
          >
            <span
              class="account-image-slot"
              aria-hidden="true"
            />
            <span class="account-card-text">
              <strong class="account-card-name">{{ name || "Ton profil" }}</strong>
              <span class="account-card-line">CV, compétences, postes recherchés</span>
            </span>
            <span
              class="arrow-circle"
              aria-hidden="true"
            ><AppIcon name="arrow-right" /></span>
          </RouterLink>
          <button
            type="button"
            class="account-image-button"
            aria-label="Changer ton image"
            aria-haspopup="dialog"
            data-test="account-image"
            @click="picking = true"
          >
            <ProfileImage
              :choice="image.choice.value"
              :initials="initials || image.initials.value"
              :size="52"
            />
            <span
              class="account-image-badge"
              aria-hidden="true"
            ><AppIcon name="pencil" /></span>
          </button>
        </div>
      </section>
      <AvatarPicker
        :open="picking"
        @close="picking = false"
      />

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

      <!-- Lot 18 (§10.4 ; maquettes Compte et CompteSombre) : des blocs à sur-titre, une ligne à flèche (D29) par
           élément. « Recherche et outils » n'est pas dessiné : ses réglages restent, dans un bloc à part. -->
      <section
        class="block account-block"
        aria-labelledby="account-path"
      >
        <h2
          id="account-path"
          class="block-cap"
        >
          Mon parcours
        </h2>
        <div class="account-group">
          <BlockRow
            title="Formations"
            to="/bilan/formations"
            data-test="account-trainings"
          />
          <BlockRow
            title="CV et lettres"
            :lines="cvCount === null ? [] : [plural(cvCount, 'document', 'documents')]"
            :to="{ path: '/profil', query: { onglet: 'parcours' } }"
            data-test="account-cv"
          />
        </div>
      </section>

      <section
        class="block account-block"
        aria-labelledby="account-prefs"
      >
        <h2
          id="account-prefs"
          class="block-cap"
        >
          Préférences
        </h2>
        <div class="account-group">
          <BlockRow
            title="Critères de recherche"
            :lines="['Postes, lieux, taux d’activité']"
            to="/profil"
            data-test="account-criteria"
          />
          <BlockRow
            title="Notifications"
            :to="rubric('notifications')"
            data-test="account-notifications"
          />
          <BlockRow
            title="Apparence"
            :lines="[THEME_LABEL[theme]]"
            :to="rubric('affichage')"
            data-test="account-appearance"
          />
        </div>
      </section>

      <section
        class="block account-block"
        aria-labelledby="account-tools"
      >
        <h2
          id="account-tools"
          class="block-cap"
        >
          Recherche et outils
        </h2>
        <div class="account-group">
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
          <!-- Venu du menu du compte (C2). La démo ne collecte rien (docs/72). -->
          <BlockRow
            v-if="me && !me.demo"
            title="Collecter maintenant"
            :lines="[running ? 'Relève en cours…' : 'Relever tout de suite les offres des sites suivis']"
            :aria-busy="running || undefined"
            :aria-disabled="running || undefined"
            data-test="account-collect"
            @click="running || collectNow()"
          />
        </div>
      </section>
      <!-- L'état de la collecte, dit aux lecteurs d'écran ; la ligne le montre à l'écran. -->
      <p
        v-if="me && !me.demo"
        class="visually-hidden"
        role="status"
        data-test="account-collect-status"
      >
        {{ running ? "Relève en cours…" : collectMessage }}
      </p>

      <section
        class="block account-block"
        aria-labelledby="account-privacy"
      >
        <h2
          id="account-privacy"
          class="block-cap"
        >
          Confidentialité et aide
        </h2>
        <div class="account-group">
          <BlockRow
            title="Mes données"
            :to="rubric('donnees')"
            data-test="account-data"
          />
          <!-- Les comptes Apple, Google ou Microsoft liés (docs/65, complément du 2026-11-05). -->
          <BlockRow
            v-if="me?.auth_enabled && !me.demo"
            title="Connexions"
            :to="rubric('connexions')"
            data-test="account-connections"
          />
          <BlockRow
            title="Ce qui part à l'IA"
            :to="{ path: '/tes-donnees', hash: '#ia' }"
            data-test="account-ai-data"
          />
          <a
            v-if="operatorEmail"
            :href="`mailto:${operatorEmail}`"
            class="block-row small"
            data-test="account-help"
          >
            <span class="block-row-text"><span class="block-row-title">Aide et contact</span></span>
            <span
              class="arrow-circle"
              aria-hidden="true"
            ><AppIcon name="external" /></span>
          </a>
          <BlockRow
            v-else
            title="Aide et contact"
            to="/a-propos"
            data-test="account-help"
          />
          <BlockRow
            v-if="showDiagnostic"
            title="État du service"
            to="/reglages/diagnostic"
            data-test="account-diagnostic"
          />
        </div>
      </section>
      <!-- Prompt du 9 novembre, PR 8 (Compte, CompteSombre) : « Se déconnecter » dans sa propre carte, en rouge, avec
           l'adresse e-mail dessous. -->
      <section
        v-if="me?.auth_enabled && phone"
        class="block account-block account-logout-block"
      >
        <div class="account-group">
          <button
            type="button"
            class="block-row small account-logout-row"
            data-test="logout"
            @click="signOut"
          >
            <AppIcon name="logout" />
            <span class="block-row-text">
              <span class="block-row-title">Se déconnecter</span>
              <span
                v-if="image.email.value"
                class="block-row-line"
                data-test="logout-email"
              >{{ image.email.value }}</span>
            </span>
          </button>
        </div>
      </section>
      <!-- Ordinateur : inchangé (MODIFICATIONS_9 ordinateur, §4), le lien rouge sous les blocs. -->
      <button
        v-else-if="me?.auth_enabled"
        type="button"
        class="account-logout account-page-logout"
        data-test="logout"
        @click="signOut"
      >
        <AppIcon name="logout" />Se déconnecter
      </button>
    </div>
  </section>
</template>
