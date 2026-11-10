<script setup lang="ts">
import { computed, ref } from "vue";

import type { OrpMonth, OrpRow } from "../api/client";
import { formatMonth, orpLeftLine } from "../format";
import AppIcon from "./AppIcon.vue";
import BlockRow from "./BlockRow.vue";
import LiquidCircle from "./LiquidCircle.vue";
import "../blocks.css";

// Maquette du 9 novembre (Orp, OrpSombre, Explorer ; §11) : à côté du cercle, le mois puis « Encore 2 d’ici le
// 5 décembre », l'échéance ORP reportée au jour ouvrable du canton ; plus de « n recherches à faire » ni de note
// sur la conseillère.
// Le suivi ORP du mois en blocs, sur téléphone (MODIFICATIONS du 8 novembre au soir, lot 18, §10.2 ; maquettes Orp,
// OrpSombre et l'onglet ORP d'Explorer) : l'objectif et le cercle liquide ; « À déclarer à l'ORP », les candidatures
// envoyées pas encore déclarées dans Job-Room, chacune vers sa fiche « Pour l'ORP » ; « Recherches du mois », celles
// qui sont déclarées, puis « Exporter le formulaire (PDF) ».
const props = defineProps<{ data: OrpMonth }>();
const emit = defineEmits<{ open: [applicationId: number]; export: [] }>();

const SHOWN = 3;
const monthName = computed(() => formatMonth(props.data.month).split(" ")[0]!.replace(/^./, (c) => c.toUpperCase()));

const toDeclare = computed(() => props.data.rows.filter((row) => !row.declared_at));
const declared = computed(() => props.data.rows.filter((row) => row.declared_at));
const allShown = ref(false);
const visible = computed(() => (allShown.value ? toDeclare.value : toDeclare.value.slice(0, SHOWN)));

// « 02.11.2026 » du formulaire : « 2 novembre » et « 2 nov. ».
function day(row: OrpRow, style: "long" | "short"): string {
  const [d, m, y] = row.date.split(".").map(Number);
  if (!d || !m || !y) return row.date;
  return new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: style }).format(new Date(y, m - 1, d));
}
const how = (method: string) => (/^[ée]lectronique$/i.test(method.trim()) ? "En ligne" : method.charAt(0).toUpperCase() + method.slice(1));
const ficheTo = (row: OrpRow) => ({ path: `/bilan/orp/candidature/${row.application_id}`, query: { mois: props.data.month } });
</script>

<template>
  <div
    class="orp-blocks"
    data-test="orp-blocks"
  >
    <section
      class="block info orp-blocks-goal"
      data-test="orp-goal"
    >
      <LiquidCircle
        v-if="data.target"
        :count="data.count"
        :target="data.target"
        :size="96"
      />
      <div>
        <p class="block-cap">
          {{ monthName }}
        </p>
        <h2
          v-if="data.target"
          class="block-title"
          data-test="orp-left"
        >
          {{ orpLeftLine(data.count, data.target, data.month, data.due_date) }}
        </h2>
        <template v-else>
          <h2 class="block-title">
            Indique ton objectif ORP
          </h2>
          <p class="block-help">
            Le nombre de recherches que l’ORP te demande chaque mois.
          </p>
          <RouterLink
            :to="{ path: '/reglages', query: { rubrique: 'recherche' } }"
            class="block-link"
          >
            Indiquer mon objectif ›
          </RouterLink>
        </template>
      </div>
    </section>

    <section
      v-if="toDeclare.length"
      class="block"
      aria-labelledby="orp-declare-title"
      data-test="orp-to-declare"
    >
      <h2
        id="orp-declare-title"
        class="block-title"
      >
        À déclarer à l’ORP · {{ toDeclare.length }}
      </h2>
      <p class="block-help">
        Envoyées, pas encore sur ta feuille de recherches.
      </p>
      <div class="orp-blocks-rows">
        <BlockRow
          v-for="row in visible"
          :key="row.application_id"
          :title="row.company"
          :status="row.missing.length ? { text: 'infos à compléter', tone: 'todo' } : null"
          :lines="[`${row.job_title} · ${how(row.method)}`, `Envoyée le ${day(row, 'long')}`]"
          :to="ficheTo(row)"
          :data-test="`orp-declare-${row.application_id}`"
        />
      </div>
      <button
        v-if="!allShown && toDeclare.length > SHOWN"
        type="button"
        class="link orp-blocks-more"
        data-test="orp-declare-more"
        @click="allShown = true"
      >
        {{ toDeclare.length - SHOWN === 1 ? "Afficher l’autre" : `Afficher les ${toDeclare.length - SHOWN} autres` }}
      </button>
    </section>

    <section
      class="block"
      aria-labelledby="orp-month-title"
      data-test="orp-searches"
    >
      <h2
        id="orp-month-title"
        class="block-title"
      >
        Recherches du mois · {{ declared.length }}
      </h2>
      <p
        class="block-help"
        data-test="orp-proof-note"
      >
        L’ORP peut demander un justificatif pour chaque recherche : l’e-mail de confirmation ou une capture.
      </p>
      <div class="orp-blocks-rows">
        <BlockRow
          v-for="row in declared"
          :key="row.application_id"
          :title="row.company"
          :status="row.missing.length ? { text: 'justificatif à joindre', tone: 'todo' } : { text: 'justificatif joint', tone: 'ok' }"
          :lines="[`${day(row, 'short')} · ${row.job_title}`]"
          :data-test="`orp-row-${row.application_id}`"
          @click="emit('open', row.application_id)"
        />
      </div>
      <button
        type="button"
        class="secondary action-2 block-action"
        data-test="orp-export"
        @click="emit('export')"
      >
        <AppIcon name="download" />Exporter le formulaire (PDF)
      </button>
    </section>
  </div>
</template>

<style>
/* Valeurs du HTML de la maquette Orp : blocs à 12 des bords, cercle de 96 et 16 d'écart, sur-titre à 4 du titre. */
.orp-blocks { --orp-blocks-16: 16px; }
.orp-blocks-goal { display: flex; align-items: center; gap: var(--orp-blocks-16); }
.orp-blocks-goal .block-cap { margin-bottom: var(--space-1); }
.orp-blocks-rows { margin-top: var(--space-4); }
.orp-blocks-more { min-height: var(--target-min); margin-top: var(--space-2); font-weight: var(--weight-bold); }
.orp-blocks .block-row.small { min-height: var(--row-72); }
</style>
<style>
/* L'onglet ORP de Bilan sur téléphone : sous les onglets, les sections sur le fond crème (D28 revu le 9 novembre). */
.bilan-orp-blocks.band { padding: var(--space-2) 0 var(--space-12); background: var(--bg); border-top: 0; }
.bilan-orp-blocks > .container { padding-left: var(--block-gutter); padding-right: var(--block-gutter); }
.bilan-orp-blocks .bilan-orp { gap: 0; }
@media screen { .bilan-orp-blocks .orp-sheet-tab:not(:has(.notice)) { display: none; } }
</style>
<style>
/* Le Suivi ORP du mois sur téléphone (maquette Orp) : l'en-tête sur --bg, puis les blocs à 12 des bords. */
.jobs-body.orp-page-blocks { padding-top: 0; gap: var(--block-gap); padding-left: var(--block-gutter); padding-right: var(--block-gutter); }
.orp-page-blocks .orp-export-row { justify-content: flex-end; }
.orp-page-blocks .orp-page-head .icon-button { color: var(--primary-text); }
.orp-page-blocks .orp-page-head h1 { font-weight: var(--weight-heavy); }
/* Version du 9 novembre (§2.9, maquette Orp) : en-tête de 64 px à 20 px des bords (retour de 44 px, 8 px avant le
   titre 22/28) ; tout ce qui n’est pas un bloc (mois, bandeau, « ⋯ », « Ajouter une recherche ») garde aussi 20 px. */
.orp-page-blocks { --orp-page-64: 64px; --orp-page-28: 28px; }
.orp-page-blocks .orp-page-head { gap: var(--space-2); min-height: var(--orp-page-64); margin: 0; padding: var(--space-3) var(--space-5); }
.orp-page-blocks .orp-page-head h1 { font-size: var(--font-section); line-height: var(--orp-page-28); }
.orp-page-blocks .orp-page-head .icon-button { width: var(--target-min); height: var(--target-min); }
.orp-page-blocks > :not(.orp-page-head, .orp-blocks, .sent-detail) { margin-left: var(--space-5); margin-right: var(--space-5); }
</style>
