<script setup lang="ts">
import { computed, useId } from "vue";
import { RouterLink, useRouter, type RouteLocationRaw } from "vue-router";

import { colorIndex, scoreWord } from "../format";

// La Ligne d'offre (planche « Ligne d'offre », composant 179:2912), la même partout : le logo ou
// l'initiale, le poste en gras, « entreprise · lieu » en gris, puis au bout de la ligne le verdict et
// l'action. Elle remplace .today-row, .offer-row et .application-row (NN/g : même nature, même
// traitement).
// - `compact` (Aujourd'hui, Suivi) : le verdict est un mot dans sa couleur ; l'action en lien accent.
// - `full` (Offres) : le verdict est ScoreWord (slot `verdict`) ; « Il te manque : … » sous le lieu.
// - Une candidature : au lieu du verdict, son état sous le titre, en orange s'il faut agir.
// Toute la ligne est un vrai lien (`to`) ou un bouton (sans `to`, elle sélectionne : `select`), nommé
// par le poste et l'entreprise (WCAG 2.4.4) ; l'action reste un bouton à part (§3, clic direct).
const props = withDefaults(
  defineProps<{
    variant?: "compact" | "full";
    title: string;
    company?: string | null;
    location?: string | null;
    // Le logo de l'entreprise (une offre qui en a un) ; sinon l'initiale, colorée par son nom.
    logo?: string | null;
    score?: number | null;
    // La ligne grise sous le lieu (« Il te manque : … ») ; `alert` la passe en orange.
    note?: string | null;
    alert?: boolean;
    // L'état d'une candidature, à la place du verdict ; `urgent` : il faut agir (orange).
    state?: string | null;
    urgent?: boolean;
    action?: string | null;
    // Le repère de l'action dans les tests (« card-step-follow-up » : quelle étape est proposée).
    actionTest?: string;
    to?: RouteLocationRaw | null;
    selected?: boolean;
  }>(),
  {
    variant: "compact",
    company: null,
    location: null,
    logo: null,
    score: null,
    note: null,
    alert: false,
    state: null,
    urgent: false,
    action: null,
    actionTest: "offer-line-action",
    to: null,
    selected: false,
  },
);
const emit = defineEmits<{ select: []; action: [] }>();

const id = useId();
const router = useRouter();
// Toute la ligne ouvre (le lien est étiré sur elle) ; un clic ailleurs que sur le lien ou l'action
// fait la même chose.
function onRowClick(event: MouseEvent): void {
  if (event.target instanceof Element && event.target.closest("a, button")) return;
  if (props.to) void router.push(props.to);
  else emit("select");
}
const name = computed(() => props.company ?? props.title);
const initial = computed(() => name.value.trim().charAt(0).toUpperCase() || "?");
const sub = computed(() => [props.company, props.location].filter(Boolean).join(" · "));
const verdict = computed(() => (props.score === null || props.score === undefined ? null : scoreWord(props.score)));
const label = computed(() => [props.title, props.company].filter(Boolean).join(", "));
const described = computed(() => [`${id}-sub`, props.note || props.state ? `${id}-more` : "", verdict.value ? `${id}-verdict` : ""].filter(Boolean).join(" "));
</script>

<template>
  <article
    :class="['offer-line', variant, { selected, 'has-action': !!action }]"
    data-test="offer-line"
    @click="onRowClick"
  >
    <span
      :class="['logo', logo ? 'image' : `c${colorIndex(name)}`]"
      aria-hidden="true"
    >
      <img
        v-if="logo"
        :src="logo"
        alt=""
        loading="lazy"
      >
      <template v-else>{{ initial }}</template>
    </span>
    <span class="offer-line-text">
      <span class="offer-line-head">
        <RouterLink
          v-if="to"
          :to="to"
          class="offer-line-title"
          :aria-label="label"
          :aria-describedby="described"
          data-test="offer-line-open"
        >{{ title }}</RouterLink>
        <button
          v-else
          type="button"
          class="offer-line-title"
          :aria-label="label"
          :aria-describedby="described"
          :aria-pressed="selected"
          data-test="offer-line-open"
          @click="emit('select')"
        >{{ title }}</button>
        <slot name="badges" />
      </span>
      <span
        :id="`${id}-sub`"
        class="offer-line-sub"
      >{{ sub }}</span>
      <span
        v-if="state"
        :id="`${id}-more`"
        :class="['offer-line-state', { urgent }]"
        data-test="offer-line-state"
      >{{ state }}</span>
      <span
        v-else-if="note"
        :id="`${id}-more`"
        :class="['offer-line-note', { alert }]"
        data-test="offer-line-note"
      ><slot name="note">{{ note }}</slot></span>
    </span>
    <span
      v-if="$slots.verdict || verdict"
      :id="`${id}-verdict`"
      class="offer-line-verdict"
    >
      <slot name="verdict">
        <span :class="['offer-line-word', verdict!.tone]">{{ verdict!.word }}</span>
      </slot>
    </span>
    <button
      v-if="action"
      type="button"
      class="link offer-line-action"
      :data-test="actionTest"
      @click="emit('action')"
    >
      {{ action }}
    </button>
  </article>
</template>
