<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type OrpMonth } from "../api/client";
import { dateInSentence } from "../dates";
import { formatMonth, ofMonth, plural, shiftMonth } from "../format";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import OrpSheet from "./OrpSheet.vue";
import TaskCheck from "./TaskCheck.vue";

// « Justificatifs déjà remis à l'ORP » (récapitulatif du 11 novembre, PR 29 ; maquettes Orp et BilanOrdinateur) :
// en tête du Bilan › ORP (ordinateur) et du Suivi ORP (téléphone), la carte du mois précédent. Tant qu'il n'est
// pas marqué remis : « Justificatifs d’octobre à remettre », le nombre de recherches et l'échéance, « Exporter le
// PDF » et « Déjà remis ». Ensuite : « Octobre remis à l’ORP », la date de remise, et « Annuler ».
// Rien à remettre (aucune recherche ce mois-là) : pas de carte.
// Bilan sur ordinateur (`wide`, maquette du 13.11 BilanOrdinateur, état octDone) : une fois remis, le bandeau vert
// « octobre est remis ! » en Caveat Brush, la date et le nombre de recherches, « Annuler », puis le personnage au dossier.
// Avant la remise, sur ordinateur (§63 du 17.11) : le bandeau pêche sans bordure, « Exporter le PDF » en bouton plein,
// « Déjà remis » en lien.
// Téléphone (§58 et §61 du 17.11, planches Orp et OrpSombre) : une tâche à cocher. La section « En retard » (ou « À
// remettre » avant l'échéance) et son badge, puis la ligne : le cercle coche le mois comme remis, le reste de la ligne
// ouvre la feuille « Exporter le PDF » / « Je l’ai déjà remis ». Remis : « Remis », « Remis le … » et « Annuler »,
// jamais de texte barré.
const props = defineProps<{ wide?: boolean }>();
const emit = defineEmits<{ changed: [month: OrpMonth] }>();

const data = ref<OrpMonth | null>(null);
const busy = ref(false);
const failed = ref(false);
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);

function previousMonth(): string {
  const now = new Date();
  return shiftMonth(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`, -1);
}
async function load(): Promise<void> {
  const { data: month } = await api.GET("/api/orp", { params: { query: { month: previousMonth() } } }).catch(() => ({ data: undefined }));
  data.value = month ?? null;
}
onMounted(() => void load());

const shown = computed(() => (data.value && data.value.count > 0 && data.value.state !== "en_cours" ? data.value : null));
const done = computed(() => shown.value?.state === "remis");
const banner = computed(() => done.value && props.wide);
const searches = computed(() => plural(shown.value?.count ?? 0, "recherche", "recherches"));
const monthName = computed(() => (shown.value ? formatMonth(shown.value.month).split(" ")[0]!.replace(/^./, (c) => c.toUpperCase()) : ""));
const dueLine = computed(() => {
  const d = shown.value;
  if (!d) return "";
  const due = new Date(`${d.due_date}T23:59:59`);
  return `${searches.value} · échéance ${due.getTime() < Date.now() ? "passée " : ""}${dateInSentence(`${d.due_date}T12:00:00`)}`;
});
const doneLine = computed(() => {
  const d = shown.value;
  if (!d?.submitted_at) return searches.value;
  return `${dateInSentence(d.submitted_at).replace(/^l/, "L")} · ${searches.value}`;
});

const late = computed(() => !!shown.value?.due_date && new Date(`${shown.value.due_date}T23:59:59`).getTime() < Date.now());
const dueDay = computed(() => (shown.value?.due_date ? dateInSentence(`${shown.value.due_date}T12:00:00`) : ""));
const taskName = computed(() => (shown.value ? `Justificatifs ${ofMonth(shown.value.month)}` : ""));
const taskLine = computed(() => {
  const d = shown.value;
  if (!d) return "";
  if (done.value) return d.submitted_at ? `Remis ${dateInSentence(d.submitted_at)}` : "Remis";
  return late.value ? `En retard depuis ${dueDay.value}` : `À remettre avant ${dueDay.value}`;
});
const sheetLine = computed(() => `${searches.value} à remettre à ton ORP. L’échéance ${late.value ? "était" : "est"} ${dueDay.value}.`);
const sheetOpen = ref(false);
function markFromSheet(): void {
  sheetOpen.value = false;
  void mark(true);
}

async function mark(submitted: boolean): Promise<void> {
  const d = shown.value;
  if (!d || busy.value) return;
  busy.value = true;
  failed.value = false;
  try {
    const params = { params: { path: { month: d.month } } };
    const { error } = submitted ? await api.PUT("/api/orp/{month}/submission", params) : await api.DELETE("/api/orp/{month}/submission", params);
    if (error !== undefined) throw new Error();
    await load();
    if (data.value) emit("changed", data.value);
  } catch {
    failed.value = true;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div
    v-if="shown"
    class="orp-proof"
  >
    <section
      v-if="!wide"
      class="orp-task"
      role="status"
      aria-labelledby="orp-task-title"
      data-test="orp-proof"
    >
      <h2
        id="orp-task-title"
        class="orp-task-title"
        data-test="orp-proof-title"
      >
        {{ done ? "Remis" : late ? "En retard" : "À remettre" }}<span
          v-if="!done"
          class="orp-task-count"
        >1</span>
      </h2>
      <div :class="['orp-task-row', { done }]">
        <TaskCheck
          :checked="done"
          :label="done ? `Annuler : ${taskName.toLowerCase()} pas encore remis` : `Marquer les ${taskName.toLowerCase()} comme remis`"
          tone="late"
          :busy="busy"
          data-test="orp-proof-check"
          @toggle="mark"
        />
        <span
          v-if="done"
          class="orp-task-text"
        >
          <strong>{{ taskName }}</strong>
          <span data-test="orp-proof-line">{{ taskLine }}</span>
        </span>
        <button
          v-else
          type="button"
          class="orp-task-open"
          aria-haspopup="dialog"
          data-test="orp-proof-open"
          @click="sheetOpen = true"
        >
          <span class="orp-task-text">
            <strong>{{ taskName }}</strong>
            <span data-test="orp-proof-line">{{ taskLine }}</span>
          </span>
          <AppIcon name="chevron" />
        </button>
        <button
          v-if="done"
          type="button"
          class="orp-proof-undo"
          :disabled="busy"
          data-test="orp-proof-undo"
          @click="mark(false)"
        >
          Annuler
        </button>
      </div>
      <p
        v-if="failed"
        class="orp-task-error"
        role="alert"
      >
        Rien n’a été enregistré. Réessaie.
      </p>
      <BottomSheet
        :open="sheetOpen"
        :title="taskName"
        data-test="orp-proof-sheet"
        @close="sheetOpen = false"
      >
        <p class="orp-task-sheet-line">
          {{ sheetLine }}
        </p>
        <button
          type="button"
          class="primary orp-task-sheet-action"
          data-test="orp-proof-export"
          @click="sheetOpen = false; sheet?.printPdf()"
        >
          Exporter le PDF
        </button>
        <button
          type="button"
          class="orp-task-sheet-link"
          data-test="orp-proof-mark"
          @click="markFromSheet"
        >
          Je l’ai déjà remis
        </button>
      </BottomSheet>
    </section>
    <section
      v-else
      :class="['orp-proof-card', { done, banner }]"
      role="status"
      aria-labelledby="orp-proof-title"
      data-test="orp-proof"
    >
      <AppIcon
        v-if="!banner"
        :name="done ? 'check-circle' : 'alert-circle'"
      />
      <div class="orp-proof-text">
        <h2
          id="orp-proof-title"
          data-test="orp-proof-title"
        >
          {{ banner ? `${monthName.toLowerCase()} est remis !` : done ? `${monthName} remis à l’ORP` : `Justificatifs ${ofMonth(shown.month)} à remettre` }}
        </h2>
        <p data-test="orp-proof-line">
          {{ done ? doneLine : dueLine }}
        </p>
        <p
          v-if="failed"
          class="orp-proof-error"
          role="alert"
        >
          Rien n’a été enregistré. Réessaie.
        </p>
      </div>
      <button
        v-if="done"
        type="button"
        class="orp-proof-undo"
        :disabled="busy"
        data-test="orp-proof-undo"
        @click="mark(false)"
      >
        Annuler
      </button>
      <div
        v-else
        class="orp-proof-actions"
      >
        <button
          type="button"
          class="primary"
          data-test="orp-proof-export"
          @click="sheet?.printPdf()"
        >
          Exporter le PDF
        </button>
        <button
          type="button"
          class="orp-proof-mark"
          :disabled="busy"
          data-test="orp-proof-mark"
          @click="mark(true)"
        >
          Déjà remis
        </button>
      </div>
      <img
        v-if="banner"
        class="orp-proof-art"
        src="/troupe/remis-224.webp"
        width="113"
        height="112"
        alt=""
        aria-hidden="true"
        data-test="orp-proof-art"
      >
    </section>
    <OrpSheet
      ref="sheet"
      :data="shown"
      @reload="load"
    />
  </div>
</template>

<style>
/* Ordinateur : la carte du mois précédent (récapitulatif du 11 novembre, PR 29 ; planche BilanOrdinateur). Avant la
   remise (§63 du 17.11) : bandeau pêche sans bordure, « Exporter le PDF » plein, « Déjà remis » en lien. Remis : le
   bandeau vert « octobre est remis ! ». Sorti de style.css : ces règles ne servent qu'ici. */
.orp-proof-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4) var(--space-5); border: 0; border-radius: var(--radius-card); background: var(--peach-soft); }
.orp-proof-card > .icon { flex: none; width: 20px; height: 20px; stroke-width: 2.2; color: var(--peach-text); }
.orp-proof-text { flex: 1; min-width: 0; }
.orp-proof-text h2 { margin: 0; font-size: var(--font-body); line-height: calc(var(--space-5) + var(--space-1) / 2); font-weight: var(--weight-bold); }
.orp-proof-text p { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-semibold); color: var(--peach-text); }
.orp-proof-text p.orp-proof-error, .orp-task-error { font-weight: var(--weight-regular); color: var(--danger-text, var(--danger)); }
.orp-proof-actions { display: flex; align-items: center; gap: var(--space-2); }
.orp-proof-actions button { height: var(--target-min); min-height: var(--target-min); padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--font-label); font-weight: var(--weight-bold); white-space: nowrap; }
.orp-proof-actions button.orp-proof-mark, button.orp-proof-mark:hover:not(:disabled) { padding: 0 var(--space-3); border: 0; background: transparent; color: var(--primary-text); box-shadow: none; }
button.orp-proof-undo, button.orp-proof-undo:hover:not(:disabled) { flex: none; height: var(--target-min); min-height: var(--target-min); padding: 0 var(--space-3); border: 0; background: transparent; color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); box-shadow: none; }
.orp-proof-card.banner { gap: var(--space-5); padding: var(--space-5) var(--space-6); border-radius: var(--space-5); background: var(--success-wash); }
.orp-proof-card.banner h2 { display: inline-block; font-family: var(--font-hand); font-size: var(--space-8); line-height: calc(var(--space-8) + var(--space-1)); font-weight: var(--weight-regular); color: var(--success); transform: rotate(-2deg); transform-origin: left center; }
.orp-proof-card.banner .orp-proof-text p { margin-top: var(--space-3); font-size: var(--font-label); line-height: calc(var(--space-5) + var(--space-1) / 2); font-weight: var(--weight-regular); color: var(--text-lead); }
.orp-proof-art { flex: none; width: auto; height: 112px; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .orp-proof-card.banner { background: var(--success-soft); } }
:root[data-theme="dark"] .orp-proof-card.banner { background: var(--success-soft); }
@media screen { .orp-proof > .orp-sheet-tab { display: none; } }

/* Téléphone (§58 du 17.11, planches Orp et OrpSombre) : titre 18/24 800 et badge de 22 px ; ligne-tâche de 76 px,
   blanche, filet de 1,5 px, rayon 18 ; nom 16/22 gras, ligne 14/20 brun. Mis sur la grille de 4 : 12 px sous le titre
   (10 sur la planche), marges intérieures 6,5 et 14,5 (+ le filet) au lieu de −9 et 14, 4 px entre les deux lignes. */
.orp-task { --task-badge: #B4631F; --task-badge-text: #FFFFFF; --task-row: 76px; --task-badge-size: 22px; --task-pad-l: 6.5px; --task-pad-r: 14.5px; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .orp-task { --task-badge: var(--peach-text); --task-badge-text: var(--on-action); } }
:root[data-theme="dark"] .orp-task { --task-badge: var(--peach-text); --task-badge-text: var(--on-action); }
.orp-page-head + .orp-proof { margin-bottom: var(--space-3); }
.orp-task-title { display: flex; align-items: center; gap: var(--space-2); margin: 0 var(--space-1) var(--space-3); font-size: var(--font-title); line-height: var(--space-6); font-weight: var(--weight-heavy); }
.orp-task-count { display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; min-width: var(--task-badge-size); height: var(--task-badge-size); padding: 0 var(--space-2); border-radius: var(--radius-pill); background: var(--task-badge); color: var(--task-badge-text); font-size: var(--font-caption); font-weight: var(--weight-heavy); }
.orp-task-row { display: flex; align-items: center; gap: var(--space-1); box-sizing: border-box; min-height: var(--task-row); padding: 0 var(--task-pad-r) 0 var(--task-pad-l); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); background: var(--surface); }
.orp-task-open, .orp-task-open:hover:not(:disabled) { flex: 1; min-width: 0; display: flex; align-items: center; gap: var(--space-3); min-height: var(--task-row); padding: 0; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--text); font: inherit; text-align: left; white-space: normal; }
.orp-task-open > .icon { flex: none; width: 20px; height: 20px; stroke-width: 2.4; color: #8C8478; }
.orp-task-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.orp-task-text > strong { font-size: var(--font-body); line-height: calc(var(--space-5) + var(--space-1) / 2); font-weight: var(--weight-bold); color: var(--text); }
.orp-task-text > span { font-size: var(--font-small); line-height: var(--space-5); color: var(--peach-text); }
.orp-task-row.done .orp-task-text > span { color: var(--text-secondary); }
.orp-task-row button.orp-proof-undo { padding: 0 var(--space-2); }
.orp-task-error { margin: var(--space-2) var(--space-1) 0; font-size: var(--font-small); }
.orp-task-sheet-line { margin: 0 0 var(--space-4); font-size: var(--font-label); line-height: calc(var(--space-5) + var(--space-1) / 2); color: var(--text-secondary); }
.orp-task-sheet-action, .orp-task-sheet-link { --task-sheet-h: 52px; width: 100%; height: var(--task-sheet-h); min-height: var(--task-sheet-h); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
button.orp-task-sheet-link, button.orp-task-sheet-link:hover:not(:disabled) { margin-top: var(--space-2); border: 0; background: transparent; box-shadow: none; color: var(--primary-text); }
</style>
