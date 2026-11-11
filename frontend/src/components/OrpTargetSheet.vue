<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "../api/client";
import "../sheet-float.css";
import BottomSheet from "./BottomSheet.vue";

// « Objectif du mois » (lot du 11 novembre au soir, PR 50 ; maquettes ProfilOrdinateurObjectif, ProfilTelObjectif et
// ProfilTelObjectifSombre) : la personne fixe elle-même le nombre de recherches que l'ORP lui demande. Un compteur
// de 1 à 99 (décision de Kevin du 11 novembre), « moins » et « plus » ronds de 56 px, le nombre en 56/60 800. Le
// compteur est un `spinbutton` : flèches haut et bas, Début et Fin. Aux bornes, le bouton concerné est désactivé et
// une phrase le dit. « Enregistrer » n'écrit que l'objectif ; un mois déjà remis garde le sien (serveur).
const MIN = 1;
const MAX = 99;
// Sans objectif encore fixé : le départ des premiers pas.
const START = 10;

const props = defineProps<{ open: boolean; target: number | null }>();
const emit = defineEmits<{ close: []; saved: [target: number] }>();

const count = ref(START);
const busy = ref(false);
const message = ref("");
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    count.value = Math.min(MAX, Math.max(MIN, props.target ?? START));
    message.value = "";
  },
  { immediate: true },
);

const month = computed(() => new Intl.DateTimeFormat("fr-CH", { month: "long", timeZone: "Europe/Zurich" }).format(new Date()));
const bound = computed(() => (count.value >= MAX ? `${MAX} est le maximum.` : count.value <= MIN ? `${MIN} est le minimum.` : ""));

function set(value: number): void {
  count.value = Math.min(MAX, Math.max(MIN, value));
}
function onKey(event: KeyboardEvent): void {
  const moves: Record<string, number> = { ArrowUp: count.value + 1, ArrowDown: count.value - 1, Home: MIN, End: MAX };
  const next = moves[event.key];
  if (next === undefined) return;
  event.preventDefault();
  set(next);
}

async function save(): Promise<void> {
  if (busy.value) return;
  if (count.value === props.target) {
    emit("close");
    return;
  }
  busy.value = true;
  message.value = "";
  try {
    // Les réglages s'enregistrent en entier : on relit, puis on ne change que l'objectif.
    const current = await api.GET("/api/settings");
    if (!current.data) throw new Error("réglages illisibles");
    const { data } = await api.PUT("/api/settings", { body: { ...current.data, orp_monthly_target: count.value } });
    if (!data) {
      message.value = "L’enregistrement a échoué. Réessaie.";
      return;
    }
    emit("saved", data.orp_monthly_target ?? count.value);
    emit("close");
  } catch {
    message.value = "L’enregistrement a échoué. Réessaie.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Objectif du mois"
    float
    class="goal-sheet"
    data-test="goal-sheet"
    @close="emit('close')"
  >
    <div class="goal">
      <p class="goal-lead">
        Le nombre de recherches que ton conseiller ORP te demande chaque mois.
      </p>
      <div class="goal-counter">
        <button
          type="button"
          class="goal-step"
          aria-label="Une recherche de moins"
          :disabled="count <= MIN"
          data-test="goal-less"
          @click="set(count - 1)"
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          ><path d="M5 12h14" /></svg>
        </button>
        <div
          class="goal-value"
          role="spinbutton"
          tabindex="0"
          aria-label="Recherches par mois"
          :aria-valuenow="count"
          :aria-valuemin="MIN"
          :aria-valuemax="MAX"
          data-test="goal-value"
          @keydown="onKey"
        >
          <span class="goal-number">{{ count }}</span>
          <span class="goal-unit">recherches par mois</span>
        </div>
        <button
          type="button"
          class="goal-step"
          aria-label="Une recherche de plus"
          :disabled="count >= MAX"
          data-test="goal-more"
          @click="set(count + 1)"
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          ><path d="M5 12h14M12 5v14" /></svg>
        </button>
      </div>
      <p
        class="goal-bound"
        role="status"
        data-test="goal-bound"
      >
        {{ bound }}
      </p>
      <p
        class="goal-note"
        data-test="goal-note"
      >
        S’applique dès {{ month }}. Les mois déjà remis ne changent pas.
      </p>
      <p
        v-if="message"
        class="goal-error"
        role="alert"
        data-test="goal-error"
      >
        {{ message }}
      </p>
    </div>
    <template #actions>
      <button
        type="button"
        class="goal-action goal-cancel"
        data-test="goal-cancel"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="goal-action goal-save"
        :aria-busy="busy || undefined"
        data-test="goal-save"
        @click="save"
      >
        Enregistrer
      </button>
    </template>
  </BottomSheet>
</template>

<style>
/* Non « scoped » : le pied est rendu dans la feuille. Tout est sous `.goal-sheet`. Valeurs du HTML des maquettes :
   phrase 15/22 ; compteur 24 px dessous, écart 24 ; boutons ronds de 56 px, bordure 1,5 px #C9C5BA, fond blanc,
   trait de 22 px ; nombre 56/60 800, « recherches par mois » 14/20 ; encadré 24 px dessous, #E8ECFB, rayon 14,
   12 px 16 px, 14/20 ; pied 52 px, rayon 26, 16/700, écart 12. */
.goal-sheet { --goal-56: 56px; --goal-60: 60px; --goal-52: 52px; --goal-26: 26px; --goal-22: 22px; --goal-15: 0.9375rem; --goal-14: 14px; --goal-96: 96px; --goal-line: #C9C5BA; }
:root[data-theme="dark"] .goal-sheet { --goal-line: #4E473E; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .goal-sheet { --goal-line: #4E473E; } }
.goal-sheet .goal { display: flex; flex-direction: column; }
.goal-sheet .goal-lead { margin: 0; font-size: var(--goal-15); line-height: var(--goal-22); color: var(--text-lead); }
.goal-sheet .goal-counter { display: flex; align-items: center; justify-content: center; gap: var(--space-6); margin-top: var(--space-6); }
.goal-sheet .goal-step { flex: none; display: flex; align-items: center; justify-content: center; box-sizing: border-box; width: var(--goal-56); height: var(--goal-56); min-height: 0; padding: 0; border: 1.5px solid var(--goal-line); border-radius: 50%; background: var(--surface); color: var(--text); }
.goal-sheet .goal-step:disabled { opacity: 0.4; cursor: default; }
.goal-sheet .goal-step svg { width: var(--goal-22); height: var(--goal-22); fill: none; stroke: currentColor; stroke-width: 2.6; stroke-linecap: round; }
.goal-sheet .goal-value { min-width: var(--goal-96); text-align: center; border-radius: var(--space-3); }
.goal-sheet .goal-number { display: block; font-size: var(--goal-56); line-height: var(--goal-60); font-weight: var(--weight-heavy); }
.goal-sheet .goal-unit { display: block; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); }
/* La phrase de la borne tient dans les 24 px qui séparent le compteur de l'encadré. */
.goal-sheet .goal-bound { min-height: var(--space-5); margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); text-align: center; color: var(--text-lead); }
.goal-sheet .goal-note { margin: 0; padding: var(--space-3) var(--space-4); border-radius: var(--goal-14); background: var(--primary-soft); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); }
.goal-sheet .goal-error { margin: var(--space-3) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--down-text); }
.goal-sheet .sheet-actions { gap: var(--space-3); }
.goal-sheet .goal-action { flex: 1 1 0; justify-content: center; text-align: center; box-sizing: border-box; height: var(--goal-52); min-height: 0; padding: 0; border-radius: var(--goal-26); font-size: var(--font-body); font-weight: var(--weight-bold); }
.goal-sheet .goal-cancel { border: 1.5px solid var(--goal-line); background: var(--surface); color: var(--text); }
.goal-sheet .goal-save { border: 0; background: var(--action); color: var(--on-action); }
</style>
