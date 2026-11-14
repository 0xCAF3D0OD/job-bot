<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api, type OrpRow } from "../api/client";
import { dateInSentence } from "../dates";
import { ofMonth, plural } from "../format";
import AppIcon from "./AppIcon.vue";
import CopyField from "./CopyField.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import "../blocks.css";

// « Pour l'ORP », une candidature à déclarer, sur téléphone (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3 ;
// maquettes OrpFiche et OrpFicheSombre). Ouverte depuis une ligne « À déclarer » du Suivi ORP ou depuis le détail
// d'une candidature envoyée. Les champs de Job-Room à recopier (D32), puis « Marquer comme déclarée ». Le même
// contenu sert la page du téléphone (OrpFicheView) et le panneau latéral de 480 px sur ordinateur.
const JOB_ROOM = "https://www.job-room.ch";

// `wide` : le panneau du Bilan sur ordinateur (maquette du 13.11, BilanOrdinateurFiche). « Ouvrir Job-Room » passe dans
// l'en-tête du panneau (BilanOrpView) ; la candidature en deux lignes sous un trait ; l'encadré « Il manque l'adresse »
// si elle manque ; les champs en lignes plates, sans blocs ; « Lien de l'annonce » quand il est connu.
const props = defineProps<{ applicationId: number; month?: string; wide?: boolean }>();
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
const search = computed<Field[]>(() => {
  const fields: Field[] = [
    { label: "Date", value: value("Date") },
    { label: "Mode", value: value("Mode"), choice: true },
    { label: "Poste", value: value("Désignation du poste") },
  ];
  const link = value("Lien vers le formulaire en ligne");
  if (props.wide && link) fields.push({ label: "Lien de l’annonce", value: link });
  return fields;
});
// Ordinateur : « Ingénieur DevOps · envoyée le 22 octobre » ; le mois de la recherche pour la phrase du bas.
const wideLine = computed(() => {
  const r = row.value;
  const day = sentDay.value;
  return r ? [r.job_title, day ? `envoyée ${dateInSentence(day.toISOString())}` : ""].filter(Boolean).join(" · ") : "";
});
const rowMonth = computed(() => {
  const day = sentDay.value;
  return day ? `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}` : (props.month ?? "");
});
const noteText = computed(() => (props.wide && rowMonth.value ? `Elle passe dans « Recherches ${ofMonth(rowMonth.value)} ».` : "Elle passe dans « Recherches du mois »."));
const addressMissing = computed(() => !!row.value?.missing.length);
// Les champs vides de la fin se lisent sur une seule ligne « Non renseigné » (maquette : « Case postale · Personne
// contactée »).
const company = computed<Field[]>(() => {
  const fields: Field[] = [
    { label: "Nom", value: value("Entreprise") },
    { label: props.wide ? "Rue et numéro" : "Rue et n°", value: [value("Rue"), value("N°")].filter(Boolean).join(" ") },
    { label: "NPA et lieu", value: value("NPA / Lieu") },
    { label: "Pays", value: value("Pays"), choice: true },
  ];
  const optional = [
    { label: "Case postale", value: value("Numéro de case postale") },
    { label: "Personne contactée", value: value("Personne contactée") },
  ];
  // Ordinateur (BilanOrdinateurFiche) : la case postale seulement si elle est connue, la personne contactée toujours.
  if (props.wide) return [...fields, ...optional.filter((f) => f.value || f.label === "Personne contactée")];
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
  <div :class="['blocks-page', 'orp-fiche-content', { 'orp-fiche-wide': wide }]">
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
        <template v-if="wide">
          <div
            class="orp-fiche-who"
            data-test="orp-fiche-who"
          >
            <strong>{{ row.company }}</strong>
            <span data-test="orp-fiche-sent">{{ wideLine }}</span>
          </div>
          <div
            v-if="addressMissing"
            class="orp-fiche-missing"
            role="note"
            data-test="orp-fiche-address-missing"
          >
            <strong>Il manque l’adresse de l’entreprise</strong>
            <span>L’ORP la demande. Complète-la ci-dessous avant de déclarer.</span>
          </div>
        </template>
        <section
          v-if="!wide"
          class="block"
        >
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
        <section
          v-if="!wide"
          class="block"
        >
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
          :class="{ block: !wide }"
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
            :tick="wide ? 'Case à cocher dans Job-Room' : undefined"
          />
        </section>
        <section
          :class="{ block: !wide }"
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
            :tick="wide ? 'Case à cocher dans Job-Room' : undefined"
          >
            <!-- « Compléter » (Kevin, 14.11, DECISIONS.md) : le mécanisme de « Ajouter » de l’écran de fin (§8), la
                 candidature envoyée à modifier, le curseur dans l’adresse. Jamais bloquant. -->
            <template
              v-if="wide && addressMissing && f.label === 'Rue et numéro' && !f.value"
              #action
            >
              <RouterLink
                :to="{ path: '/candidatures/suivi', query: { candidature: String(row.application_id), modifier: 'adresse' } }"
                class="orp-fiche-complete"
                data-test="orp-fiche-complete"
              >
                Compléter<span class="visually-hidden"> l’adresse de l’entreprise</span>
              </RouterLink>
            </template>
          </CopyField>
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
        <p
          class="orp-fiche-note"
          data-test="orp-fiche-note"
        >
          {{ noteText }}
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
.orp-fiche-content { --fiche-52: 52px; flex: 1; display: flex; flex-direction: column; }
.orp-fiche-body { flex: 1; padding: var(--block-gap) var(--block-gutter) var(--space-6); }
.orp-fiche-bar { position: sticky; bottom: 0; padding: var(--space-3) var(--space-4) calc(var(--space-4) + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line); }
.orp-fiche-declare { justify-content: center; width: 100%; min-height: var(--fiche-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.orp-fiche-note, .orp-fiche-done { margin: var(--space-2) 0 0; font-size: var(--font-small); text-align: center; color: var(--text-secondary); }
.orp-fiche-done { margin: 0; }
/* Téléphone (§2.9, 9 novembre) : la barre aussi à 20 px des bords (maquette OrpFiche, padding 12 20 16). */
@media (max-width: 820px) { .orp-fiche-bar { padding-left: var(--space-5); padding-right: var(--space-5); } }
/* Bilan sur ordinateur (maquette du 13.11, BilanOrdinateurFiche) : contenu à 24 px des bords, sans blocs ; lignes de
   56 px séparées d'un trait, libellé 13/16, valeur 16/22 demi-grasse sur une ligne ; boutons copier de 40 px. */
.orp-fiche-wide { --fw-2: 2px; --fw-6: 6px; --fw-12: 12px; --fw-18: 18px; --fw-22: 22px; --fw-missing-pad: 14.5px 18.5px; background: var(--bg); }
.orp-fiche-wide .orp-fiche-body { padding: var(--space-1) var(--space-6) var(--space-6); }
.orp-fiche-who { padding-bottom: var(--space-5); border-bottom: 1px solid var(--line); }
.orp-fiche-who strong { display: block; font-size: var(--fw-18); line-height: var(--space-6); }
.orp-fiche-who span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.orp-fiche-missing { margin-top: var(--space-5); padding: var(--fw-missing-pad); background: var(--peach-wash); border: 1.5px solid color-mix(in srgb, var(--peach) 55%, var(--surface)); border-radius: var(--radius-card); }
.orp-fiche-missing strong { display: block; font-size: var(--font-label); line-height: var(--space-5); color: var(--peach-text); }
.orp-fiche-missing span { display: block; margin-top: var(--fw-2); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-tertiary); }
.orp-fiche-wide .block-cap { margin: var(--space-6) 0 var(--space-1); }
.orp-fiche-wide .block-field { gap: var(--space-4); min-height: 56px; padding: var(--fw-6) 0; box-sizing: border-box; border-top-color: var(--line); }
.orp-fiche-wide .block-cap + .block-field { padding-top: var(--fw-6); }
.orp-fiche-wide .block-field-label { line-height: var(--space-4); }
.orp-fiche-wide .block-field-value { margin-top: var(--fw-2); line-height: var(--fw-22); font-weight: var(--weight-semibold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; overflow-wrap: normal; }
.orp-fiche-wide .block-field-value.block-field-none { font-weight: var(--weight-regular); }
.orp-fiche-wide .block-tick { margin-top: var(--fw-6); padding: var(--fw-2) var(--space-2); border-radius: var(--fw-6); background: var(--surface-muted); font-size: var(--fw-12); line-height: var(--space-4); color: var(--text-tertiary); }
.orp-fiche-complete { flex: none; display: flex; align-items: center; min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.orp-fiche-wide .copy-button { width: 40px; height: 40px; color: var(--primary-text); }
.orp-fiche-wide .orp-fiche-bar { padding: var(--space-4) var(--space-6) var(--space-5); }
.side-panel-head:has(> .orp-fiche-job-room) h2 { flex: 1; }
.side-panel-head:has(> .orp-fiche-job-room) .side-panel-close { margin-left: 0; }
.orp-fiche-job-room { --fj-6: 6px; --fj-14: 14px; flex: none; display: inline-flex; align-items: center; gap: var(--fj-6); height: 40px; padding: 0 var(--fj-14); border: 1.5px solid var(--primary-graphic); border-radius: var(--radius-pill); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.orp-fiche-job-room .icon { width: 16px; height: 16px; }
/* Ordinateur (lot 18, §10.3) : dans le panneau latéral de 480 px, les blocs sur leur fond et la barre en bas. */
.side-panel-body:has(> .orp-fiche-content) { display: flex; flex-direction: column; padding: 0; }
.side-panel-body > .orp-fiche-content { flex: 1 0 auto; }
</style>
