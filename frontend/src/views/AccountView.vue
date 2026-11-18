<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import AccountLine from "../components/AccountLine.vue";
import PageHero from "../components/PageHero.vue";
import ProfileImage from "../components/ProfileImage.vue";
import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { useProfileImage } from "../composables/useProfileImage";
import { useProfiles } from "../composables/useProfiles";
import { useTheme } from "../composables/useTheme";

// Prompt du 9 novembre, PR 8 (maquettes Compte et CompteSombre) : une carte par groupe (profil ; Mon parcours ;
// Préférences ; Confidentialité et aide ; Se déconnecter), lignes séparées par un trait fin, comme Réglages ; plus de
// trait entre les groupes, 12 px au-dessus et au-dessous de chacun.
// La page Compte (maquette Compte, docs/139 étape 10a ; décisions de Kevin du 2026-11-05) : le sommaire de tout ce
// qui te concerne, sur téléphone comme sur ordinateur. La carte du profil, puis Mon parcours, Préférences,
// Recherche et outils (absent de la maquette, C8), Confidentialité et aide. Chaque ligne ouvre sa page ou sa
// rubrique des Réglages.
const { me, logout } = useAuth();
const router = useRouter();
const route = useRoute();

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
// Les valeurs à droite des lignes (§51) : « Auto », « Clair », « Sombre », comme la planche.
const THEME_LABEL = { auto: "Auto", light: "Clair", dark: "Sombre" } as const;
const owner = computed(() => Boolean(me.value?.is_owner));
// L’exploitant n’a pas de formule : « Sans limite », pas « Essentiel » (audit du 17.11, N2).
const planName = computed(() => (plan.value?.unlimited ? "Sans limite" : plan.value?.plan === "plus" ? "Plus" : "Essentiel"));
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

// « Formations · 2 en cours » (Kevin, 17.11 13 h 40) : un petit appel qui ne retarde pas la page. La ligne s’affiche
// tout de suite, le nombre la rejoint quand il arrive, sans indicateur ; en cas d’échec ou à 0, « Formations › » seul.
const trainingsInProgress = ref(0);
async function loadTrainings(): Promise<void> {
  try {
    const { data } = await api.GET("/api/trainings/in-progress");
    trainingsInProgress.value = data?.in_progress ?? 0;
  } catch {
    trainingsInProgress.value = 0;
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

// Retour sur la ligne d’origine (accord de Kevin du 17.11, K39) : la ligne cliquée et le défilement sont gardés pour
// la session ; au retour d’une rubrique ou d’État du service, la page revient à ce défilement et met le focus clavier
// sur la ligne, au lieu de remonter en haut.
const RETURN_KEY = "jobA1-retour-ligne";
function rememberRow(event: MouseEvent): void {
  const row = (event.target as HTMLElement).closest<HTMLElement>(":is(a, button)[data-test^=account-]");
  if (!row || row.dataset.test === "account-collect") return;
  try {
    sessionStorage.setItem(RETURN_KEY, JSON.stringify({ path: route.path, test: row.dataset.test, y: row.getBoundingClientRect().top }));
  } catch {
    // Stockage refusé (navigation privée) : on revient en haut, comme avant.
  }
}
function restoreRow(): void {
  let saved: { path?: string; test?: string; y?: number } | null = null;
  try {
    saved = JSON.parse(sessionStorage.getItem(RETURN_KEY) ?? "null");
  } catch {
    return;
  }
  // Venu d’une rubrique : par le lien de retour (back) ou par le retour du navigateur (forward).
  const { back, forward } = (history.state ?? {}) as { back?: unknown; forward?: unknown };
  const fromRubric = [back, forward].some((path) => typeof path === "string" && path.startsWith("/reglages"));
  if (!saved || saved.path !== route.path || !fromRubric) return;
  try {
    sessionStorage.removeItem(RETURN_KEY);
  } catch {
    // rien à effacer
  }
  const { test, y = 0 } = saved;
  requestAnimationFrame(() => {
    // La ligne à la même hauteur dans la fenêtre qu’au moment du clic.
    const row = document.querySelector<HTMLElement>(`[data-test="${test}"]`);
    if (!row) return;
    scrollBy(0, row.getBoundingClientRect().top - y);
    row.focus({ preventScroll: true });
  });
}

onMounted(() => {
  restoreRow();
  void loadName();
  void loadCvCount();
  void loadContact();
  void loadTrainings();
  void load();
  void image.load();
});
</script>

<template>
  <PageHero title="Compte" />
  <!-- LISEZMOI §51 du 17.11 (planches Compte, CompteSombre, CompteImage) : la ligne profil, puis des groupes de lignes
       d’une seule ligne de texte, 56 px, la valeur utile à droite avant le chevron, une couleur par icône de section.
       « Recherche et outils », Connexions, État du service et le choix du profil d’essai ne sont pas dessinés : gardés
       (règle 3 de CLAUDE.md), au même style. -->
  <section
    class="band account-v2"
    @click.capture="rememberRow"
  >
    <div
      class="container account-page"
      data-test="account-page"
    >
      <RouterLink
        to="/profil"
        class="account-profile"
        data-test="account-profile-card"
      >
        <span
          class="account-image"
          data-test="account-image"
        >
          <ProfileImage
            :choice="image.choice.value"
            :initials="initials || image.initials.value"
            :size="48"
          />
        </span>
        <span class="account-profile-text">
          <strong class="account-profile-name">{{ name || "Ton profil" }}</strong>
          <span class="account-profile-line">Mon profil et mon CV</span>
        </span>
        <span
          class="account-line-chevron"
          aria-hidden="true"
        ><AppIcon name="chevron" /></span>
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

      <section
        class="account-block"
        aria-labelledby="account-path"
      >
        <h2
          id="account-path"
          class="account-cap"
        >
          Mon parcours
        </h2>
        <div class="account-group">
          <AccountLine
            title="Formations"
            :value="trainingsInProgress > 0 ? `${trainingsInProgress} en cours` : undefined"
            to="/bilan/formations"
            icon="graduation"
            tone="violet"
            data-test="account-trainings"
          />
          <AccountLine
            title="CV et lettres"
            :value="cvCount === null ? undefined : String(cvCount)"
            :to="{ path: '/profil', query: { onglet: 'parcours' } }"
            icon="file"
            tone="blue"
            data-test="account-cv"
          />
        </div>
      </section>

      <section
        class="account-block"
        aria-labelledby="account-prefs"
      >
        <h2
          id="account-prefs"
          class="account-cap"
        >
          Préférences
        </h2>
        <div class="account-group">
          <AccountLine
            title="Critères de recherche"
            to="/profil"
            icon="search"
            tone="green"
            data-test="account-criteria"
          />
          <AccountLine
            title="Notifications"
            :to="rubric('notifications')"
            icon="bell"
            tone="peach"
            data-test="account-notifications"
          />
          <AccountLine
            title="Apparence"
            :value="THEME_LABEL[theme]"
            :to="rubric('affichage')"
            icon="moon"
            data-test="account-appearance"
          />
        </div>
      </section>

      <section
        class="account-block"
        aria-labelledby="account-tools"
      >
        <h2
          id="account-tools"
          class="account-cap"
        >
          Recherche et outils
        </h2>
        <div class="account-group">
          <AccountLine
            title="Objectif ORP et sites"
            :to="rubric('recherche')"
            icon="flag"
            data-test="account-orp"
          />
          <AccountLine
            title="Rythme"
            :to="rubric('rythme')"
            icon="clock"
            data-test="account-rhythm"
          />
          <AccountLine
            title="IA"
            :to="rubric('ia')"
            icon="ai"
            data-test="account-ai"
          />
          <AccountLine
            title="Agenda"
            :to="rubric('outils')"
            icon="calendar"
            data-test="account-tools"
          />
          <AccountLine
            title="Formule"
            :value="planName"
            :to="rubric('formule')"
            icon="tag"
            data-test="account-plan"
          />
          <AccountLine
            v-if="owner"
            title="Administration"
            :to="rubric('plateforme')"
            icon="settings"
            data-test="account-admin"
          />
          <!-- Venu du menu du compte (C2). La démo ne collecte rien (docs/72). -->
          <AccountLine
            v-if="me && !me.demo"
            title="Collecter maintenant"
            :value="running ? 'En cours…' : undefined"
            :aria-busy="running || undefined"
            :aria-disabled="running || undefined"
            icon="refresh"
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
        class="account-block"
        aria-labelledby="account-privacy"
      >
        <h2
          id="account-privacy"
          class="account-cap"
        >
          Confidentialité et aide
        </h2>
        <div class="account-group">
          <AccountLine
            title="Mes données"
            :to="rubric('donnees')"
            icon="database"
            data-test="account-data"
          />
          <!-- Les comptes Apple, Google ou Microsoft liés (docs/65, complément du 2026-11-05). -->
          <AccountLine
            v-if="me?.auth_enabled && !me.demo"
            title="Connexions"
            :to="rubric('connexions')"
            icon="plug"
            data-test="account-connections"
          />
          <AccountLine
            title="L’IA et tes données"
            :to="{ path: '/tes-donnees', hash: '#ia' }"
            icon="shield"
            data-test="account-ai-data"
          />
          <!-- « Aide » (§51) : l'« Aide et contact » d'avant, l'e-mail de l'exploitant ou la page À propos. -->
          <AccountLine
            title="Aide"
            :href="operatorEmail ? `mailto:${operatorEmail}` : undefined"
            :to="operatorEmail ? undefined : '/a-propos'"
            icon="help"
            data-test="account-help"
          />
          <AccountLine
            v-if="showDiagnostic"
            title="État du service"
            to="/reglages/diagnostic"
            icon="activity"
            data-test="account-diagnostic"
          />
        </div>
      </section>
      <!-- « Se déconnecter » dans sa propre carte, en rouge, l’adresse e-mail dessous (inchangé au §51). -->
      <div
        v-if="me?.auth_enabled && phone"
        class="account-group account-logout-group"
      >
        <button
          type="button"
          class="account-logout-row"
          data-test="logout"
          @click="signOut"
        >
          <AppIcon name="logout" />
          <span class="account-logout-text">
            <span class="account-logout-title">Se déconnecter</span>
            <span
              v-if="image.email.value"
              class="account-logout-email"
              data-test="logout-email"
            >{{ image.email.value }}</span>
          </span>
        </button>
      </div>
      <!-- Ordinateur : le lien rouge sous les blocs (MODIFICATIONS_9 ordinateur, §4). -->
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

<style>
/* La page Compte (LISEZMOI §51 du 17.11 ; planches Compte, CompteSombre). Valeurs de la planche posées sur la grille de
   4 (audit-grille) : 14 px → 16 px d'écart et de marge, titres de groupe 18 px → 20 px au-dessus. */
.account-v2 { --acc-cap: 13px; --acc-cap-lh: 18px; --acc-name: 17px; --acc-name-lh: 24px; --acc-line-lh: 20px; --acc-title-lh: 22px; --acc-value: 15px; --acc-chevron: 24px; --acc-chevron-icon: 20px; }
.account-v2.band { padding: var(--space-3) 0 var(--space-12); border-top: 0; }
.account-v2 > .container { padding: 0 var(--space-5); }
.account-v2 .account-page { display: grid; gap: 0; max-width: 40rem; }
.account-v2 .account-cap { margin: var(--space-5) var(--space-1) var(--space-2); font-size: var(--acc-cap); line-height: var(--acc-cap-lh); font-weight: var(--weight-bold); letter-spacing: .05em; text-transform: uppercase; color: var(--text-secondary); }
.account-v2 :is(.account-profile, .account-group) { background: var(--surface); border: 1px solid var(--row-sep); border-radius: var(--radius-card); overflow: hidden; }
.account-v2 .account-profile { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4); color: var(--text); text-decoration: none; }
.account-v2 .account-image { flex: none; display: inline-flex; }
.account-v2 .account-image .profile-image { color: var(--avatar-initials); box-shadow: none; }
.account-v2 .account-profile-text { display: grid; flex: 1; min-width: 0; }
.account-v2 .account-profile-name { font-size: var(--acc-name); line-height: var(--acc-name-lh); overflow-wrap: anywhere; }
.account-v2 .account-profile-line { font-size: var(--font-small); line-height: var(--acc-line-lh); color: var(--text-secondary); }
.account-line { display: flex; align-items: center; gap: var(--space-4); box-sizing: border-box; width: 100%; min-height: 56px; margin: 0; padding: 0 var(--space-4); border: 0; background: transparent; font: inherit; text-align: left; color: var(--text); text-decoration: none; cursor: pointer; }
.account-line + .account-line { border-top: 1px solid var(--line-soft); }
.account-line-icon { flex: none; width: 22px; height: 22px; stroke-width: 2; color: var(--row-icon); }
.account-line-icon.violet { color: var(--agency-text); }
.account-line-icon.blue { color: var(--primary-graphic); }
.account-line-icon.green { color: var(--success); }
.account-line-icon.peach { color: var(--icon-peach); }
.account-line-title { flex: 1; min-width: 0; font-size: var(--font-body); line-height: var(--acc-title-lh); font-weight: var(--weight-semibold); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-line-value { flex: none; font-size: var(--acc-value); color: var(--text-secondary); }
/* Le chevron des listes (LISEZMOI §49) : 20 px, trait 2,4, --chevron, dans une zone de 24 px. */
.account-v2 .account-line-chevron { flex: none; display: grid; place-items: center; width: var(--acc-chevron); height: var(--acc-chevron); margin-left: calc(var(--space-2) * -1); color: var(--chevron); }
.account-v2 .account-line-chevron .icon { width: var(--acc-chevron-icon); height: var(--acc-chevron-icon); stroke-width: 2.4; }
.account-line[aria-disabled="true"] { cursor: progress; }
.account-v2 .account-switch { margin-top: var(--space-4); }
.account-v2 .account-logout-group { margin-top: var(--space-6); }
.account-logout-row { display: flex; align-items: center; gap: var(--space-4); box-sizing: border-box; width: 100%; min-height: 56px; padding: var(--space-2) var(--space-4); border: 0; background: transparent; font: inherit; text-align: left; cursor: pointer; }
.account-logout-row > .icon { flex: none; width: var(--space-6); height: var(--space-6); color: var(--logout-text); }
.account-logout-text { display: grid; min-width: 0; }
.account-logout-title { font-weight: var(--weight-bold); line-height: var(--acc-title-lh); color: var(--logout-text); }
.account-logout-email { font-size: var(--font-small); line-height: var(--acc-line-lh); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-v2 .account-page-logout { justify-self: start; margin: var(--space-4) var(--space-4) 0; padding: 0; }
</style>
