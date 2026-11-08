<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { dateInList } from "../dates";
import { plural } from "../format";
import { useAuth } from "../composables/useAuth";
import { useDismissLayer } from "../composables/useDismissLayer";
import { useProfileImage } from "../composables/useProfileImage";
import { useProfiles } from "../composables/useProfiles";
import { useTheme, type Theme } from "../composables/useTheme";
import AppIcon from "./AppIcon.vue";
import ProfileImage from "./ProfileImage.vue";
import SegmentedControl from "./SegmentedControl.vue";
import SidePanel from "./SidePanel.vue";

// Le panneau du compte (maquette du 8 novembre, docs/143, D24 ; remplace le menu « Compte, Se déconnecter » de
// docs/89) : l'image choisie, en haut à droite de l'ordinateur, ouvre un panneau latéral non modal de 420 px.
// En-tête : l'image (48 px), le nom et l'e-mail. « Mon compte » (profil et CV, alertes e-mail, réglages),
// « Affichage » (le mode sombre, appliqué tout de suite), « Aide », puis « Se déconnecter » en pied.
const router = useRouter();
const { me, logout } = useAuth();
// Le profil affiché est lu dès l'ouverture de l'app (le bandeau « Revenir à … »).
const { load } = useProfiles();
const image = useProfileImage();
const { theme, setTheme } = useTheme();
const layer = useDismissLayer("compte");
const trigger = ref<HTMLButtonElement | null>(null);

const cvDate = ref<string | null>(null);
const searches = ref<number | null>(null);
const operatorEmail = ref<string | null>(null);

const label = computed(() => (image.firstName.value ? `Compte de ${image.firstName.value}` : "Compte"));
const themeModel = computed({ get: () => theme.value, set: (value: string) => setTheme(value as Theme) });
const THEMES = [
  { value: "light", label: "Clair" },
  { value: "auto", label: "Auto" },
  { value: "dark", label: "Sombre" },
];

// Les lignes de détail se lisent à l'ouverture : la date du dernier CV et le nombre de recherches suivies.
async function loadDetails(): Promise<void> {
  const [docs, alerts, privacy] = await Promise.all([
    api.GET("/api/documents").catch(() => ({ data: undefined })),
    api.GET("/api/alert-searches").catch(() => ({ data: undefined })),
    api.GET("/api/privacy").catch(() => ({ data: undefined })),
  ]);
  const cvs = (docs.data ?? []).filter((doc) => doc.kind !== "certificate").map((doc) => doc.uploaded_at).sort();
  cvDate.value = cvs.length ? dateInList(cvs[cvs.length - 1]!) : null;
  searches.value = alerts.data ? alerts.data.searches.filter((search) => search.active).length : null;
  operatorEmail.value = privacy.data?.contact?.match(/[\w.+-]+@[\w-]+\.[\w.-]+/)?.[0] ?? null;
}

const accountRows = computed(() => [
  {
    to: "/profil",
    icon: "user" as const,
    title: "Mon profil et mon CV",
    detail: cvDate.value ? `CV mis à jour ${/^\d/.test(cvDate.value) ? "le " : ""}${cvDate.value}` : "CV, compétences, postes recherchés",
    test: "account-profile",
  },
  {
    to: "/candidatures/alertes",
    icon: "mail" as const,
    title: "Mes alertes e-mail",
    detail: searches.value === null ? "" : searches.value ? plural(searches.value, "recherche suivie", "recherches suivies") : "Aucune recherche suivie",
    test: "account-alerts",
  },
  { to: "/reglages", icon: "settings" as const, title: "Réglages", detail: "Notifications, connexions, données", test: "account-settings" },
]);

function toggle(): void {
  layer.toggle(trigger.value);
  if (layer.open.value) void loadDetails();
}

async function signOut(): Promise<void> {
  layer.hide(false);
  await logout();
  await router.push({ name: "news" });
}

onMounted(() => {
  void load();
  void image.load();
});
</script>

<template>
  <div class="account-menu">
    <!-- L'image choisie (ou les initiales), sans nom ni flèche. La légende reprend le nom accessible (WCAG 1.4.13). -->
    <button
      ref="trigger"
      type="button"
      class="header-round account-trigger"
      :aria-expanded="layer.open.value"
      aria-haspopup="dialog"
      :aria-label="label"
      :data-label="label"
      data-test="account-menu"
      @click="toggle"
    >
      <ProfileImage
        :choice="image.choice.value"
        :initials="image.initials.value"
        :size="40"
      />
    </button>
    <SidePanel
      modeless
      :open="layer.open.value"
      :title="image.name.value || 'Compte'"
      close-label="Fermer le compte"
      @close="layer.hide()"
    >
      <template #head="{ titleId }">
        <ProfileImage
          :choice="image.choice.value"
          :initials="image.initials.value"
          :size="48"
        />
        <div class="account-head-text">
          <h2
            :id="titleId"
            tabindex="-1"
            data-test="account-name"
          >
            {{ image.name.value || "Compte" }}
          </h2>
          <span
            v-if="image.email.value"
            class="account-head-email"
          >{{ image.email.value }}</span>
        </div>
      </template>
      <nav
        aria-label="Compte"
        data-test="account-panel"
      >
        <h3 class="panel-eyebrow">
          Mon compte
        </h3>
        <RouterLink
          v-for="row in accountRows"
          :key="row.to"
          :to="row.to"
          class="panel-row"
          :data-test="row.test"
          @click="layer.hide(false)"
        >
          <AppIcon :name="row.icon" />
          <span class="panel-row-text">
            <span class="panel-row-title">{{ row.title }}</span>
            <span
              v-if="row.detail"
              class="panel-row-detail"
            >{{ row.detail }}</span>
          </span>
          <AppIcon
            name="chevron"
            class="panel-row-chevron"
          />
        </RouterLink>
        <h3 class="panel-eyebrow">
          Affichage
        </h3>
        <div class="panel-row panel-row-static">
          <AppIcon name="moon" />
          <span class="panel-row-text panel-row-title">Mode sombre</span>
          <SegmentedControl
            v-model="themeModel"
            :options="THEMES"
            label="Mode sombre"
            data-test="account-theme"
          />
        </div>
        <h3 class="panel-eyebrow">
          Aide
        </h3>
        <component
          :is="operatorEmail ? 'a' : 'RouterLink'"
          v-bind="operatorEmail ? { href: `mailto:${operatorEmail}` } : { to: '/a-propos' }"
          class="panel-row"
          data-test="account-help"
          @click="layer.hide(false)"
        >
          <AppIcon name="help" />
          <span class="panel-row-text panel-row-title">Aide et contact</span>
          <AppIcon
            :name="operatorEmail ? 'external' : 'chevron'"
            class="panel-row-chevron"
          />
        </component>
      </nav>
      <template
        v-if="me?.auth_enabled"
        #footer
      >
        <button
          type="button"
          class="account-logout"
          data-test="logout"
          @click="signOut"
        >
          <AppIcon name="logout" />Se déconnecter
        </button>
      </template>
    </SidePanel>
  </div>
</template>
