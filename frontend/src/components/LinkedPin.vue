<script setup lang="ts">
import { ref, watch } from "vue";

import { colorIndex, initials, logoTone } from "../format";
import AppIcon from "./AppIcon.vue";
import LinkedArrow from "./LinkedArrow.vue";

// La carte choisie toujours visible (planche CandidaturesOrdinateurEpinglee, §18 du 15 novembre) : quand la vraie carte
// sort de la partie visible de la liste par le haut, cette version compacte se pose à 12 px sous la barre de filtres
// (side="top") ; par le bas, à 12 px du bas de la liste (side="bottom"). Elle est posée sur la colonne, hors de ce qui
// défile (.linked-cards).
// useLinkedNotch dit laquelle montrer (data-pinned sur la liste) ; elle porte la flèche, la pointe du rail se place en
// face d'elle. C'est un bouton : la liste défile jusqu'à la vraie carte, qui garde seule aria-current et reçoit le focus.
// `label` : le nom du bouton, s'il doit en dire plus (Rendez-vous : la date complète et l'entreprise).
const props = withDefaults(defineProps<{ side: "top" | "bottom"; title: string; sub: string; name?: string; logo?: string | null; label?: string }>(), {
  name: "",
  logo: null,
  label: "Revenir à la candidature sélectionnée dans la liste",
});
const root = ref<HTMLElement | null>(null);
// Le logo comme sur la carte (ListCard) : l'image, ou les initiales colorées si elle ne charge pas.
const logoFailed = ref(false);
watch(
  () => props.logo,
  () => (logoFailed.value = false),
);

function back(): void {
  const card = root.value?.closest(".linked-list")?.querySelector<HTMLElement>('[aria-current="true"]');
  if (!card) return;
  const calm = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  card.scrollIntoView?.({ block: "nearest", behavior: calm ? "auto" : "smooth" });
  card.focus({ preventScroll: true });
}
</script>

<template>
  <div
    ref="root"
    class="linked-pin"
    :data-side="side"
  >
    <button
      type="button"
      class="linked-pin-card"
      :aria-label="label"
      :data-test="`linked-pin-${side}`"
      @click="back"
    >
      <LinkedArrow />
      <slot name="logo">
        <span
          :class="['list-card-logo', logo && !logoFailed ? 'image' : `c${colorIndex(name || title)} t${logoTone(name || title)}`]"
          aria-hidden="true"
        >
          <img
            v-if="logo && !logoFailed"
            :src="logo"
            alt=""
            @error="logoFailed = true"
          >
          <template v-else>{{ initials(name || title) }}</template>
        </span>
      </slot>
      <span class="list-card-text">
        <span class="list-card-title">{{ title }}</span>
        <span class="list-card-sub">{{ sub }} · Sélection affichée</span>
      </span>
      <AppIcon name="chevron" />
    </button>
  </div>
</template>

<style>
/* Valeurs de la planche CandidaturesOrdinateurEpinglee : 76 px de haut, rayon 14, fond et contour de la carte choisie,
   logo de 40 (rayon 10), intitulé 16/21 sur une ligne, « Entreprise · Sélection affichée » 13/18, chevron de 20 (bleu texte),
   ombre 0 8 20 ; dessous, un fondu de la couleur de page sur 112 px (de 12 px au-dessus à 24 px en dessous). Masquée
   (donc hors du Tab) tant que la liste ne la demande pas. */
.linked-pin { --pin-12: -12px; --pin-fade: 112px; display: none; position: absolute; z-index: 3; left: var(--linked-bar); right: var(--linked-gap); height: 0; }
.linked-list[data-pinned="top"] > [data-side="top"], .linked-list[data-pinned="bottom"] > [data-side="bottom"] { display: block; }
/* Posée sur la colonne, par-dessus les cartes qui défilent : 12 px sous la barre de filtres (--linked-pin-top, mesuré)
   ou 12 px au-dessus du bas de la liste, alignée sur les cartes. */
[data-side="top"].linked-pin { top: var(--linked-pin-top); }
[data-side="bottom"].linked-pin { bottom: var(--space-3); }
.linked-pin::before { content: ""; position: absolute; left: 0; right: 0; top: var(--pin-12); height: var(--pin-fade); background: linear-gradient(var(--bg) 84%, transparent); }
[data-side="bottom"].linked-pin::before { top: auto; bottom: var(--pin-12); transform: scaleY(-1); }
.linked-pin-card {
  --card-21: 21px; --card-3: 2px; --card-12: 10px; --pin-h: 76px; --pin-18: 18px; --pin-r: 14px; --linked-card-border: 2px;
  position: absolute; left: 0; right: 0; display: flex; align-items: center; gap: var(--space-3); height: var(--pin-h); max-width: none; padding: 0 var(--space-4);
  background: var(--linked-selected-bg); border: 2px solid var(--primary-graphic); border-radius: var(--pin-r); box-shadow: 0 8px 20px rgb(27 31 42 / 14%); color: var(--text); text-align: left;
}
[data-side="bottom"] > .linked-pin-card { bottom: 0; }
.linked-pin-card:active { transform: none; }
.linked-pin-card > .list-card-logo { flex: none; width: var(--btn-compact); height: var(--btn-compact); }
.linked-pin-card .list-card-text { flex: 1; }
.linked-pin-card .list-card-sub { font-size: var(--label-caps); line-height: var(--pin-18); }
.linked-pin-card > .icon { flex: none; width: var(--space-5); height: var(--space-5); color: var(--primary-text); transform: rotate(-90deg); }
[data-side="bottom"] .icon { transform: rotate(90deg); }
</style>
