<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AppIcon from "./AppIcon.vue";

// Chercher dans le CV ou la lettre (§34 du 16.11, planche PreparerOrdinateurCVRecherche) : la barre sous l'en-tête du
// document. Les résultats sont surlignés par l'API CSS Highlight, sans toucher au texte que Vue affiche ; le résultat
// courant porte en plus un contour et la page défile jusqu'à lui. Entrée = suivant, Maj+Entrée = précédent, Échap = fermer.
const props = defineProps<{ target: HTMLElement | null; label: string }>();
const emit = defineEmits<{ close: [] }>();

const query = ref("");
const count = ref(0);
const at = ref(0);
const field = ref<HTMLInputElement | null>(null);
const box = ref<HTMLElement | null>(null);
const boxStyle = ref<Record<string, string> | null>(null);
let ranges: Range[] = [];

// Sans accents ni majuscules, lettre à lettre : les positions restent celles du texte affiché.
const fold = (text: string) =>
  text
    .split("")
    .map((c) => c.normalize("NFD").charAt(0).toLowerCase().charAt(0))
    .join("");
const marks = typeof Highlight === "undefined" ? null : CSS.highlights;

function find(keep = false): void {
  const el = props.target;
  const q = fold(query.value.trim());
  ranges = [];
  if (el && q) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      // Un texte caché (le champ remplacé par le texte à lire) ne compte pas.
      if (!node.parentElement?.getClientRects().length) continue;
      const text = fold(node.nodeValue ?? "");
      for (let i = text.indexOf(q); i >= 0; i = text.indexOf(q, i + q.length)) {
        const range = document.createRange();
        range.setStart(node, i);
        range.setEnd(node, i + q.length);
        ranges.push(range);
      }
    }
  }
  count.value = ranges.length;
  at.value = keep ? Math.min(at.value, Math.max(0, ranges.length - 1)) : 0;
  paint(!keep);
}

function paint(scroll: boolean): void {
  const now = ranges[at.value];
  marks?.set("doc-hit", new Highlight(...ranges));
  if (now) marks?.set("doc-hit-now", new Highlight(now));
  else marks?.delete("doc-hit-now");
  place();
  // Défile au plus court, seulement si le résultat est caché par la barre du haut ou les retouches du bas.
  if (scroll && now)
    void nextTick(() => {
      const r = box.value?.getBoundingClientRect();
      const down = r ? r.bottom - innerHeight + 160 : 0;
      const up = r ? r.top - 120 : 0;
      if (down > 0 || up < 0) scrollBy({ top: down > 0 ? down : up, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    });
}

// Le contour du résultat courant, placé sur la carte du document (le parent, positionné).
function place(): void {
  const card = box.value?.parentElement;
  const base = card?.getBoundingClientRect();
  const rect = ranges[at.value]?.getBoundingClientRect();
  boxStyle.value =
    card && base && rect?.width
      ? { top: `${rect.top - base.top - card.clientTop}px`, left: `${rect.left - base.left - card.clientLeft - 1}px`, width: `${rect.width + 2}px`, height: `${rect.height}px` }
      : null;
}

function go(step: 1 | -1): void {
  if (!count.value) return;
  at.value = (at.value + step + count.value) % count.value;
  paint(true);
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Enter") {
    event.preventDefault();
    go(event.shiftKey ? -1 : 1);
  }
}

watch(query, () => find());
let mutations: MutationObserver | null = null;
let sizes: ResizeObserver | null = null;
watch(
  () => props.target,
  (el) => {
    mutations?.disconnect();
    sizes?.disconnect();
    if (el) {
      mutations = new MutationObserver(() => find(true));
      mutations.observe(el, { subtree: true, childList: true, characterData: true, attributes: true });
      if (typeof ResizeObserver !== "undefined") {
        sizes = new ResizeObserver(place);
        sizes.observe(el);
      }
    }
    find(true);
  },
  { immediate: true },
);
onMounted(() => field.value?.focus());
onBeforeUnmount(() => {
  mutations?.disconnect();
  sizes?.disconnect();
  marks?.delete("doc-hit");
  marks?.delete("doc-hit-now");
});
</script>

<template>
  <div
    role="search"
    class="doc-search"
    data-test="doc-search"
    @keydown.esc.prevent="emit('close')"
  >
    <label class="doc-search-field">
      <AppIcon name="search" />
      <input
        ref="field"
        v-model="query"
        type="text"
        :aria-label="label"
        data-test="doc-search-input"
        @keydown="onKey"
      >
      <span
        class="doc-search-count"
        aria-live="polite"
        data-test="doc-search-count"
      >{{ count ? `${at + 1} sur ${count}` : query.trim() ? "0 sur 0" : "" }}</span>
    </label>
    <button
      type="button"
      class="doc-tool doc-tool-round"
      aria-label="Résultat précédent"
      :disabled="!count"
      data-test="doc-search-prev"
      @click="go(-1)"
    >
      <AppIcon name="chevron-up" />
    </button>
    <button
      type="button"
      class="doc-tool doc-tool-round"
      aria-label="Résultat suivant"
      :disabled="!count"
      data-test="doc-search-next"
      @click="go(1)"
    >
      <AppIcon name="chevron-down" />
    </button>
    <button
      type="button"
      class="doc-tool doc-tool-round doc-search-close"
      aria-label="Fermer la recherche"
      data-test="doc-search-close"
      @click="emit('close')"
    >
      <AppIcon name="close" />
    </button>
  </div>
  <i
    ref="box"
    class="doc-hit-box"
    :hidden="!boxStyle"
    :style="boxStyle ?? undefined"
    aria-hidden="true"
  />
</template>

<style>
/* §34 du 16.11 : boutons de l'en-tête (loupe ronde de 44, « Voir les changements » en pilule de 44, 15/700, contour 1,5
   --card-line ; actif : fond --primary-soft, contour --primary-graphic) et barre de recherche (10 / 18,5, trait dessous ;
   champ pilule de 44 au contour 2 px bleu, compteur 14/600 gris, boutons ronds de 44). Surlignage sur le papier, qui
   reste blanc en sombre : résultats #FFE9A8, courant #FFB86B et contour 2 px #B4631F. */
.doc-tool { --doc-44: 44px; --doc-14: 14px; display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2); height: var(--doc-44); padding: 0 var(--space-4); border: 1.5px solid var(--card-line); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.doc-tool[aria-pressed="true"], .doc-tool[aria-expanded="true"] { border-color: var(--primary-graphic); background: var(--primary-soft); color: var(--primary-text); }
.doc-tool-round { width: var(--doc-44); padding: 0; flex: none; }
.doc-tool > .icon { width: 18px; height: 18px; }
.doc-tool-mark { width: var(--doc-14); height: var(--doc-14); box-sizing: border-box; border-left: 3px solid var(--primary-graphic); border-radius: var(--space-1); background: color-mix(in srgb, var(--primary-graphic) 18%, var(--surface)); }
.doc-tools { display: flex; align-items: center; gap: var(--space-2); }
.doc-search { --doc-10: 10px; display: flex; align-items: center; gap: var(--space-2); padding: var(--doc-10) var(--prep-card); border-bottom: 1px solid var(--line); background: var(--surface); }
.doc-search-field { --doc-14: 14px; flex: 1; display: flex; align-items: center; gap: var(--space-2); height: 44px; padding: 0 var(--doc-14); box-sizing: border-box; border: 2px solid var(--card-line); border-radius: var(--radius-pill); color: var(--text-secondary); }
.doc-search-field:focus-within { border-color: var(--primary-graphic); }
.doc-search .doc-search-field > input { flex: 1; min-width: 0; height: auto; min-height: 0; padding: 0; border: 0; background: none; color: var(--text); font-size: var(--font-label); box-shadow: none; }
.doc-search-count { font-size: var(--font-small); font-weight: var(--weight-semibold); }
.doc-search-close { border: 0; background: none; }
::highlight(doc-hit) { background-color: #FFE9A8; }
::highlight(doc-hit-now) { background-color: #FFB86B; }
.doc-hit-box { --doc-2: 2px; position: absolute; border-radius: var(--doc-2); outline: 2px solid #B4631F; pointer-events: none; }
/* Pendant la recherche et « Voir les changements », les champs du document laissent place à leur texte. */
.doc-reading .screen-only { display: none; }
.doc-reading .print-only { display: revert; }
.cv-changed { margin: -1px -2px -1px -4px; padding: 1px 2px 1px 4px; border-radius: 2px; background: #E8ECFB; box-shadow: inset 2px 0 0 #2445C2; }
</style>
