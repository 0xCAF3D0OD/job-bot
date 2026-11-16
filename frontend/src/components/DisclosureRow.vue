<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Ligne dépliable (docs/32 §2.1), au style des filtres des offres : le titre, un résumé en
// gris, un chevron qui tourne ; le contenu glisse, souligné d'un trait vertical. Dans un
// même groupe, une seule ligne ouverte à la fois. En option (1.6.61) : une icône dans une pastille
// devant le titre, et une phrase en gris sous le titre (l'enseignement, visible replié).
const props = withDefaults(
  defineProps<{ title: string; value?: string; description?: string; icon?: IconName; group?: string; startOpen?: boolean }>(),
  {
    value: "",
    description: "",
    icon: undefined,
    group: "",
    startOpen: false,
  },
);
const emit = defineEmits<{ toggle: [open: boolean] }>();

const id = `disclosure-${Math.random().toString(36).slice(2, 8)}`;
const local = ref(props.startOpen);
const open = computed(() => (props.group ? openInGroup[props.group] === id : local.value));

function toggle(): void {
  const next = !open.value;
  if (props.group) openInGroup[props.group] = next ? id : null;
  else local.value = next;
}

// Le contenu reste monté (comme un <details>) : replié, il est rogné et inerte.
watch(open, (value) => emit("toggle", value));
if (props.group && props.startOpen) openInGroup[props.group] = id;
</script>

<script lang="ts">
const openInGroup = reactive<Record<string, string | null>>({});
</script>

<template>
  <section :class="['disclosure', { open }]">
    <button
      type="button"
      class="disclosure-row"
      :aria-expanded="open"
      :aria-controls="id"
      @click="toggle"
    >
      <span
        v-if="icon"
        class="disclosure-icon"
        aria-hidden="true"
      ><AppIcon :name="icon" /></span>
      <span
        v-if="description"
        class="disclosure-text"
      >
        <span class="disclosure-title">{{ title }}</span>
        <span
          class="disclosure-description"
          data-test="disclosure-description"
        >{{ description }}</span>
      </span>
      <span
        v-else
        class="disclosure-title"
      >{{ title }}</span>
      <span
        v-if="value"
        class="disclosure-value"
      >{{ value }}</span>
      <span
        class="disclosure-chevron"
        aria-hidden="true"
      ><AppIcon name="chevron" /></span>
    </button>
    <!-- Une action sur le repliable ouvert (« Masquer ») : sur la ligne du titre, pas sur une
         ligne à elle (docs/119). -->
    <div
      v-if="$slots.actions"
      v-show="open"
      class="disclosure-actions"
    >
      <slot name="actions" />
    </div>
    <div
      :id="id"
      class="disclosure-panel"
      :inert="!open"
    >
      <div class="disclosure-clip">
        <div class="disclosure-body">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.disclosure:has(> .disclosure-actions) > .disclosure-panel { grid-column: 1 / -1; }
.disclosure-list > .disclosure + .disclosure { border-top: 1px solid var(--divider); }
.disclosure.open:has(> .disclosure-actions):has(> :is(.disclosure-row, .disclosure-actions):hover) > .disclosure-row { border-top-right-radius: 0; }
.disclosure.open:has(> :is(.disclosure-row, .disclosure-actions):hover) > .disclosure-actions { border-top-right-radius: inherit; }
/* L'anneau suit les coins de la carte, même là où le repliable n'a pas de cadre (1.6.5). */
.disclosure:has(> .disclosure-row:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--radius); }
.disclosure-list > .disclosure:has(> .disclosure-row:focus-visible) { outline-offset: -2px; }
.disclosure-text .disclosure-title { font-size: var(--font-body); }
/* Ouvert et survolé, le fond passe à --accent-soft : la phrase passe en --text pour garder 4,5:1 (WCAG 1.4.3, 1.6.63). */
.disclosure.open:has(> :is(.disclosure-row, .disclosure-actions):hover) > .disclosure-row .disclosure-description { color: var(--text); }
.disclosure.open .disclosure-panel { grid-template-rows: 1fr; }
.disclosure-list > .disclosure:first-child { border-top-left-radius: var(--radius); border-top-right-radius: var(--radius); }
.disclosure-list > .disclosure:last-child { border-bottom-left-radius: var(--radius); border-bottom-right-radius: var(--radius); }
.orp-month-rows > .disclosure + .disclosure { margin-top: 0; }
/* L'action d'une ligne ouverte (« Voir sur jobs.ch ») à la marge du texte, pas collée au bord. */
.detail-panel .detail-disclosure .disclosure-actions { padding-right: var(--space-6); }
.bilan-detail .disclosure + .disclosure { margin-top: 0; }
.bilan-detail .disclosure { border-color: var(--line); border-radius: var(--radius-card); }
</style>
