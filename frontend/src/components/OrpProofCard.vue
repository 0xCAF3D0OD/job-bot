<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type OrpMonth } from "../api/client";
import { dateInSentence } from "../dates";
import { formatMonth, ofMonth, plural, shiftMonth } from "../format";
import AppIcon from "./AppIcon.vue";
import OrpSheet from "./OrpSheet.vue";

// « Justificatifs déjà remis à l'ORP » (récapitulatif du 11 novembre, PR 29 ; maquettes Orp et BilanOrdinateur) :
// en tête du Bilan › ORP (ordinateur) et du Suivi ORP (téléphone), la carte du mois précédent. Tant qu'il n'est
// pas marqué remis : « Justificatifs d’octobre à remettre », le nombre de recherches et l'échéance, « Exporter le
// PDF » et « Déjà remis ». Ensuite : « Octobre remis à l’ORP », la date de remise, et « Annuler ».
// Rien à remettre (aucune recherche ce mois-là) : pas de carte.
// Bilan sur ordinateur (`wide`, maquette du 13.11 BilanOrdinateur, état octDone) : une fois remis, le bandeau vert
// « octobre est remis ! » en Caveat Brush, la date et le nombre de recherches, « Annuler », puis le personnage au dossier.
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
          class="secondary action-2"
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
