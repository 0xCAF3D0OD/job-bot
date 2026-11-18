<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import AppIcon from "./AppIcon.vue";
import type { IconName } from "../icons";
import { api, type SiteOut } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { usePlan } from "../composables/usePlan";

// « Recherche et outils » (planche ReglagesOutils du 18.11, §70) : Recherche (Objectif ORP, Sites suivis, Collecter
// maintenant) puis Outils (IA, Agenda, Formule, Administration). Chaque ligne ouvre sa rubrique ; la valeur à droite.
// Icônes seules, gris foncé, sans cadre. La démo ne collecte rien (docs/72) ; l’Administration, à l’exploitant.
const props = defineProps<{ orpTarget?: number | null }>();
const emit = defineEmits<{ ready: [] }>();
const { me } = useAuth();
const { plan } = usePlan();
const { running, message, collectNow } = useCollect();
const router = useRouter();

const sites = ref<SiteOut[] | null>(null);
const agendaLinked = ref(false);
onMounted(async () => {
  try {
    const [sitesAnswer, tokens] = await Promise.all([
      api.GET("/api/sites").catch(() => null),
      api.GET("/api/agenda/tokens").catch(() => null),
    ]);
    sites.value = Array.isArray(sitesAnswer?.data) ? sitesAnswer.data : [];
    agendaLinked.value = Array.isArray(tokens?.data) && tokens.data.length > 0;
  } finally {
    emit("ready");
  }
});

const followed = computed(() => (sites.value ?? []).filter((site) => site.active));
const sitesLine = computed(() => {
  const names = followed.value.map((site) => site.name);
  if (!names.length) return "Aucun site suivi";
  return names.length > 3 ? `${names.slice(0, 3).join(", ")} et ${names.length - 3} autre${names.length > 4 ? "s" : ""}` : names.join(", ");
});
// « Sans limite · 42 notes ce mois » : la formule, puis les notes du mois.
const planLine = computed(() => {
  if (!plan.value) return "";
  const name = plan.value.unlimited ? "Sans limite" : plan.value.plan === "plus" ? "Plus" : "Essentiel";
  const used = plan.value.usage.find((usage) => usage.key === "score")?.used;
  return used === undefined ? name : `${name} · ${used} note${used > 1 ? "s" : ""} ce mois`;
});

type Row = { id: string; title: string; sub: string; icon: IconName; value?: string; rubrique: string };
const research = computed<Row[]>(() => [
  {
    id: "account-orp",
    title: "Objectif ORP",
    sub: "Recherches demandées par mois",
    icon: "target",
    value: props.orpTarget ? String(props.orpTarget) : "",
    rubrique: "recherche",
  },
  {
    id: "account-sites",
    title: "Sites suivis",
    sub: sitesLine.value,
    icon: "globe",
    value: sites.value ? String(followed.value.length) : "",
    rubrique: "recherche",
  },
]);
const tools = computed<Row[]>(() => [
  { id: "account-ai", title: "IA", sub: "Ce qu’elle lit et ce qu’elle écrit", icon: "spark", rubrique: "ia" },
  {
    id: "account-tools",
    title: "Agenda",
    sub: "Rendez-vous ORP et entretiens",
    icon: "calendar",
    value: agendaLinked.value ? "Connecté" : "",
    rubrique: "outils",
  },
  { id: "account-plan", title: "Formule", sub: planLine.value, icon: "banknote", rubrique: "formule" },
  ...(me.value?.is_owner
    ? [{ id: "account-admin", title: "Administration", sub: "Comptes invités, état du service", icon: "shield" as const, rubrique: "plateforme" }]
    : []),
]);
const go = (rubrique: string) => void router.push({ path: "/reglages", query: { rubrique } });
</script>

<template>
  <section
    id="recherche-outils"
    class="settings-section"
    data-test="section-recherche-outils"
  >
    <h2 class="section-title">
      Recherche
    </h2>
    <div class="rg-list rg-tools">
      <button
        v-for="row in research"
        :key="row.id"
        type="button"
        class="rg-link-row rg-link-two"
        :data-test="row.id"
        @click="go(row.rubrique)"
      >
        <AppIcon
          :name="row.icon"
          class="rg-lead"
        />
        <span class="rg-label">{{ row.title }}<span class="rg-sub">{{ row.sub }}</span></span>
        <span
          v-if="row.value"
          class="rg-value"
        >{{ row.value }}</span>
        <AppIcon name="chevron" />
      </button>
      <div
        v-if="me && !me.demo"
        class="rg-link-row rg-link-two"
        data-test="tools-collect"
      >
        <AppIcon
          name="refresh"
          class="rg-lead"
        />
        <span class="rg-label">Collecter maintenant<span
          class="rg-sub"
          role="status"
        >{{ running ? "Relève en cours…" : message || "Relever tout de suite les offres des sites suivis" }}</span></span>
        <button
          type="button"
          class="tonal rg-run"
          :aria-busy="running || undefined"
          :aria-disabled="running || undefined"
          data-test="account-collect"
          @click="running || collectNow()"
        >
          Lancer
        </button>
      </div>
    </div>
  </section>
  <section
    class="settings-section"
    data-test="section-outils-liste"
  >
    <h2 class="section-title">
      Outils
    </h2>
    <div class="rg-list rg-tools">
      <button
        v-for="row in tools"
        :key="row.id"
        type="button"
        class="rg-link-row rg-link-two"
        :data-test="row.id"
        @click="go(row.rubrique)"
      >
        <AppIcon
          :name="row.icon"
          class="rg-lead"
        />
        <span class="rg-label">{{ row.title }}<span
          v-if="row.sub"
          class="rg-sub"
        >{{ row.sub }}</span></span>
        <span
          v-if="row.value"
          class="rg-value"
        >{{ row.value }}</span>
        <AppIcon name="chevron" />
      </button>
    </div>
  </section>
</template>

<style>
.rg-run { flex: none; min-height: 44px; padding: 0 var(--space-5); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font: inherit; font-weight: var(--weight-bold); cursor: pointer; }
</style>
