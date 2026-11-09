<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api, type OrpRow } from "../api/client";
import { dateInSentence } from "../dates";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import CopyField from "./CopyField.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import "../blocks.css";

// « Pour l'ORP », une candidature à déclarer, sur téléphone (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3 ;
// maquettes OrpFiche et OrpFicheSombre). Ouverte depuis une ligne « À déclarer » du Suivi ORP ou depuis le détail
// d'une candidature envoyée. Les champs de Job-Room à recopier (D32), puis « Marquer comme déclarée ». Le même
// contenu sert la page du téléphone (OrpFicheView) et le panneau latéral de 480 px sur ordinateur.
const JOB_ROOM = "https://www.job-room.ch";

const props = defineProps<{ applicationId: number; month?: string }>();
const emit = defineEmits<{ declared: [] }>();
const id = computed(() => props.applicationId);
const month = computed(() => props.month);
const row = ref<OrpRow | null>(null);
const loaded = ref(false);
const busy = ref(false);

async function load(): Promise<void> {
  const { data } = await api.GET("/api/orp", { params: { query: month.value ? { month: month.value } : {} } });
  row.value = data?.rows.find((r) => r.application_id === id.value) ?? null;
  loaded.value = true;
}
onMounted(() => void load());
watch(() => [props.applicationId, props.month], () => void load());

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
    emit("declared");
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="blocks-page orp-fiche-content">
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
  </div>
</template>

<style>
/* Valeurs du HTML de la maquette OrpFiche : en-tête de 64 sur --bg, blocs à 12 des bords, barre du bas sur --bg avec
   un trait, bouton plein de 52, phrase de 14 centrée à 8 dessous. */
.orp-fiche { --fiche-64: 64px; --fiche-52: 52px; --fiche-22: 22px; --fiche-28: 28px; min-height: 100dvh; display: flex; flex-direction: column; }
.orp-fiche-head { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; gap: var(--space-2); min-height: var(--fiche-64); padding: var(--space-3) var(--space-5); background: var(--bg); }
.orp-fiche-head h1 { margin: 0; font-size: var(--fiche-22); line-height: var(--fiche-28); font-weight: var(--weight-heavy); }
.orp-fiche-head .icon-button { width: var(--target-min); height: var(--target-min); border: 0; background: transparent; color: var(--primary-text); }
.orp-fiche-content { flex: 1; display: flex; flex-direction: column; }
.orp-fiche-body { flex: 1; padding: var(--block-gap) var(--block-gutter) var(--space-6); }
.orp-fiche-bar { position: sticky; bottom: 0; padding: var(--space-3) var(--space-4) calc(var(--space-4) + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line); }
.orp-fiche-declare { justify-content: center; width: 100%; min-height: var(--fiche-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.orp-fiche-note, .orp-fiche-done { margin: var(--space-2) 0 0; font-size: var(--font-small); text-align: center; color: var(--text-secondary); }
.orp-fiche-done { margin: 0; }
/* Téléphone (§2.9, 9 novembre) : la barre aussi à 20 px des bords (maquette OrpFiche, padding 12 20 16). */
@media (max-width: 820px) { .orp-fiche-bar { padding-left: var(--space-5); padding-right: var(--space-5); } }
/* Ordinateur (lot 18, §10.3) : dans le panneau latéral de 480 px, les blocs sur leur fond et la barre en bas. */
.side-panel-body:has(> .orp-fiche-content) { display: flex; flex-direction: column; padding: 0; }
.side-panel-body > .orp-fiche-content { flex: 1 0 auto; }
</style>
