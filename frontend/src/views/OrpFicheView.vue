<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type OrpRow } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import CopyField from "../components/CopyField.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import { dateInSentence } from "../dates";
import { plural } from "../format";
import "../blocks.css";

// « Pour l'ORP », une candidature à déclarer, sur téléphone (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3 ;
// maquettes OrpFiche et OrpFicheSombre). Ouverte depuis une ligne « À déclarer » du Suivi ORP ou depuis le détail
// d'une candidature envoyée. Les champs de Job-Room à recopier (D32), puis « Marquer comme déclarée ».
const JOB_ROOM = "https://www.job-room.ch";

const route = useRoute();
const router = useRouter();
const id = computed(() => Number(route.params.id));
const month = computed(() => (typeof route.query.mois === "string" ? route.query.mois : undefined));
const row = ref<OrpRow | null>(null);
const loaded = ref(false);
const busy = ref(false);

async function load(): Promise<void> {
  const { data } = await api.GET("/api/orp", { params: { query: month.value ? { month: month.value } : {} } });
  row.value = data?.rows.find((r) => r.application_id === id.value) ?? null;
  loaded.value = true;
}
onMounted(() => void load());

const field = (label: string) => row.value?.job_room.find((f) => f.label === label);
const value = (label: string) => field(label)?.value?.trim() ?? "";

// « 02.11.2026 » du formulaire, en date.
const sentDay = computed(() => {
  const [d, m, y] = (row.value?.date ?? "").split(".").map(Number);
  return d && m && y ? new Date(y, m - 1, d, 12) : null;
});
const sentLine = computed(() => {
  const r = row.value;
  const day = sentDay.value;
  if (!r || !day) return "";
  const parts = [`Envoyée ${dateInSentence(day.toISOString())}`];
  const waiting = Math.floor((Date.now() - day.getTime()) / 86_400_000);
  if (/suspens/i.test(r.result) && waiting > 0) parts.push(`sans réponse depuis ${plural(waiting, "jour", "jours")}`);
  return parts.join(" · ");
});

type Field = { label: string; value: string; choice?: boolean };
const search = computed<Field[]>(() => [
  { label: "Date", value: value("Date") },
  { label: "Mode", value: value("Mode"), choice: true },
  { label: "Poste", value: value("Désignation du poste") },
]);
// Les champs vides de la fin se lisent sur une seule ligne « Non renseigné » (maquette : « Case postale · Personne
// contactée »).
const company = computed<Field[]>(() => {
  const fields: Field[] = [
    { label: "Nom", value: value("Entreprise") },
    { label: "Rue et n°", value: [value("Rue"), value("N°")].filter(Boolean).join(" ") },
    { label: "NPA et lieu", value: value("NPA / Lieu") },
    { label: "Pays", value: value("Pays"), choice: true },
  ];
  const optional = [
    { label: "Case postale", value: value("Numéro de case postale") },
    { label: "Personne contactée", value: value("Personne contactée") },
  ];
  const empty = optional.filter((f) => !f.value);
  return [...fields, ...optional.filter((f) => f.value), ...(empty.length ? [{ label: empty.map((f) => f.label).join(" · "), value: "" }] : [])];
});

async function declare(): Promise<void> {
  if (!row.value || busy.value) return;
  busy.value = true;
  try {
    await api.PUT("/api/applications/{application_id}/job-room", { params: { path: { application_id: row.value.application_id } } });
    back();
  } finally {
    busy.value = false;
  }
}
function back(): void {
  if (window.history.state?.back) router.back();
  else void router.push({ path: "/bilan/orp", query: month.value ? { mois: month.value } : {} });
}
</script>

<template>
  <section
    class="blocks-page orp-fiche"
    aria-labelledby="orp-fiche-title"
    data-test="orp-fiche"
  >
    <header class="orp-fiche-head">
      <button
        type="button"
        class="icon-button icon-only"
        aria-label="Retour"
        data-test="orp-fiche-back"
        @click="back"
      >
        <AppIcon name="arrow-left" />
      </button>
      <h1 id="orp-fiche-title">
        Pour l’ORP
      </h1>
    </header>
    <div class="orp-fiche-body">
      <LoadingBlocks
        v-if="!loaded"
        :heights="['8rem', '9rem', '14rem']"
      />
      <p
        v-else-if="!row"
        class="block block-help"
        data-test="orp-fiche-missing"
      >
        Cette candidature n’est pas dans le formulaire de ce mois.
      </p>
      <template v-else>
        <section class="block">
          <p class="block-cap">
            Candidature
          </p>
          <h2 class="block-title">
            {{ row.company }}
          </h2>
          <p class="block-help">
            {{ row.job_title }}
          </p>
          <p
            class="block-help"
            data-test="orp-fiche-sent"
          >
            {{ sentLine }}
          </p>
        </section>
        <section class="block">
          <h2 class="block-title">
            Déclarer dans Job-Room
          </h2>
          <p class="block-help">
            Recopie ces infos dans ton formulaire de recherches. Le bouton copie copie la valeur.
          </p>
          <a
            :href="JOB_ROOM"
            target="_blank"
            rel="noopener"
            class="button-link secondary action-2 block-action"
            data-test="orp-fiche-job-room"
          >Ouvrir Job-Room<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </section>
        <section
          class="block"
          aria-labelledby="orp-fiche-search"
        >
          <h2
            id="orp-fiche-search"
            class="block-cap"
          >
            La recherche
          </h2>
          <CopyField
            v-for="f in search"
            :key="f.label"
            v-bind="f"
          />
        </section>
        <section
          class="block"
          aria-labelledby="orp-fiche-company"
        >
          <h2
            id="orp-fiche-company"
            class="block-cap"
          >
            L’entreprise
          </h2>
          <CopyField
            v-for="f in company"
            :key="f.label"
            v-bind="f"
          />
        </section>
      </template>
    </div>
    <div
      v-if="row"
      class="orp-fiche-bar"
      data-test="orp-fiche-bar"
    >
      <template v-if="row.declared_at">
        <p class="orp-fiche-done">
          Déclarée dans Job-Room {{ dateInSentence(`${row.declared_at}T12:00:00`) }}.
        </p>
      </template>
      <template v-else>
        <button
          type="button"
          class="primary action-1 orp-fiche-declare"
          :disabled="busy"
          data-test="orp-fiche-declare"
          @click="declare"
        >
          Marquer comme déclarée
        </button>
        <p class="orp-fiche-note">
          Elle passe dans « Recherches du mois ».
        </p>
      </template>
    </div>
  </section>
</template>

<style>
/* Valeurs du HTML de la maquette OrpFiche : en-tête de 64 sur --bg, blocs à 12 des bords, barre du bas sur --bg avec
   un trait, bouton plein de 52, phrase de 14 centrée à 8 dessous. */
.orp-fiche { --fiche-64: 64px; --fiche-52: 52px; --fiche-22: 22px; --fiche-28: 28px; min-height: 100dvh; display: flex; flex-direction: column; }
.orp-fiche-head { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; gap: var(--space-3); min-height: var(--fiche-64); padding: var(--space-3) var(--space-4); background: var(--bg); }
.orp-fiche-head h1 { margin: 0; font-size: var(--fiche-22); line-height: var(--fiche-28); font-weight: var(--weight-heavy); }
.orp-fiche-head .icon-button { width: var(--target-min); height: var(--target-min); border: 0; background: transparent; color: var(--primary-text); }
.orp-fiche-body { flex: 1; padding: var(--block-gap) var(--block-gutter) var(--space-6); }
.orp-fiche-bar { position: sticky; bottom: 0; padding: var(--space-3) var(--space-4) calc(var(--space-4) + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line); }
.orp-fiche-declare { justify-content: center; width: 100%; min-height: var(--fiche-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.orp-fiche-note, .orp-fiche-done { margin: var(--space-2) 0 0; font-size: var(--font-small); text-align: center; color: var(--text-secondary); }
.orp-fiche-done { margin: 0; }
</style>
