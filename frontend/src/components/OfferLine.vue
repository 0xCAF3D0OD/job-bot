<script setup lang="ts">
import { computed, ref, useId, watch } from "vue";
import { RouterLink, useRouter, type RouteLocationRaw } from "vue-router";

import { usePhone } from "../composables/usePhone";
import { cityOnly, colorIndex, frenchName, initials, scoreWord } from "../format";
import { isBlankLogo } from "../logoImage";

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
// Téléphone (maquette Candidatures) : deux initiales ; ordinateur : la première lettre.
const { phone } = usePhone();
// Une image qui ne charge pas, ou vide (un carré blanc générique) : les initiales colorées à la place.
const logoFailed = ref(false);
watch(
  () => props.logo,
  () => {
    logoFailed.value = false;
  },
);
const showLogo = computed(() => !!props.logo && !logoFailed.value);
function onLogoLoad(event: Event): void {
  logoFailed.value = isBlankLogo(event.target as HTMLImageElement);
}
const initial = computed(() => (phone.value ? initials(name.value) : name.value.trim().charAt(0).toUpperCase() || "?"));
// Sur téléphone, la ville sans le canton (maquette Candidatures).
// L'entreprise, puis le lieu ; deux morceaux, pour que seule l'entreprise se coupe (« … ») et jamais la ville.
const place = computed(() => (phone.value ? cityOnly(props.location) : frenchName(props.location)) || "");
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
      :class="['logo', showLogo ? 'image' : `c${colorIndex(name)}`]"
      aria-hidden="true"
    >
      <img
        v-if="showLogo"
        :src="logo!"
        alt=""
        loading="lazy"
        @load="onLogoLoad"
        @error="logoFailed = true"
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
      ><span
        v-if="company"
        class="offer-line-company"
      >{{ company }}</span><span
        v-if="place"
        class="offer-line-place"
      >{{ company ? " · " : "" }}{{ place }}</span></span>
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
      <!-- Les faits en pastilles (taux, contrat, télétravail), sous le lieu (maquette Candidatures). -->
      <slot name="facts" />
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
    <!-- Un bouton dans un coin de la ligne (le « ⋯ » d'une carte d'offre), au-dessus de la zone qui l'ouvre. -->
    <slot name="corner" />
  </article>
</template>
