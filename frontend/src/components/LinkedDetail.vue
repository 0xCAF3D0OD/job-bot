<script lang="ts">
import type { FunctionalComponent } from "vue";

// Sans liste reliée (téléphone, tablette) : le détail tel quel, sans zone.
export const Plain: FunctionalComponent<{ list?: HTMLElement | null }> = (_props, { slots }) => slots.default?.();
Plain.props = ["list"];
</script>

<script setup lang="ts">
import { ref, toRef } from "vue";

import { useLinkedNotch } from "../composables/useLinkedNotch";

// La zone de détail reliée à la liste (Candidatures sur ordinateur, §18 du 15 novembre) : pas de fond ni de cadre, un
// rail vertical de 1,5 px (--linked-line) à 8 px de la colonne de liste (9 sur la planche), en fondu sur 56 px en haut et 72 px en bas ;
// en face de la carte choisie, le rail fait une pointe vers la gauche qui touche la pointe de la flèche (data-notch,
// tracé de la planche), le trait droit interrompu sur sa hauteur. Le rail et sa pointe restent fixes : seul le contenu défile.
const props = defineProps<{ list: HTMLElement | null }>();
const zone = ref<HTMLElement | null>(null);
const { top, visible } = useLinkedNotch(toRef(props, "list"), zone);
</script>

<template>
  <div
    ref="zone"
    class="linked-detail"
  >
    <svg
      v-show="visible"
      data-notch
      aria-hidden="true"
      class="linked-notch"
      width="24"
      height="60"
      viewBox="0 0 24 60"
      :style="{ top: `${top}px` }"
    >
      <rect
        class="linked-notch-gap"
        style="fill: var(--bg)"
        x="-0.3"
        y="7"
        width="2.1"
        height="46"
      />
      <path
        class="linked-notch-line"
        style="stroke: var(--linked-line)"
        d="M0.75 3 L0.75 7 Q0.75 12 -1.79 15.54 L-13.42 27.17 Q-16.25 30 -13.42 32.83 L-1.79 44.46 Q0.75 48 0.75 53 L0.75 57"
        fill="none"
        stroke-width="1.5"
        stroke-linejoin="round"
      />
    </svg>
    <div class="linked-scroll">
      <slot />
    </div>
  </div>
</template>

<style>
/* Valeurs de la planche CandidaturesOrdinateurB (§18, trois onglets) : colonne de liste de 504 px, cartes de 480 px
   (24 px avant la fin de la colonne), rail 9 px après la colonne sur la planche, 8 ici pour la grille de 4 (32 px après le bord des cartes ; la flèche avance d'autant, le contact reste exact) ; contenu de la zone
   à 24 px du rail, 16 px entre les cartes, 48 px sous la dernière ; barre de défilement fine, --card-line sur fond
   transparent. */
.linked-detail {
  --linked-w: 1.5px; --linked-fade-top: 56px; --linked-fade-y: 72px; --linked-into: 8px;
  position: relative; z-index: 0; display: flex; flex: 1; flex-direction: column; min-width: 0; min-height: 0;
  margin-left: var(--linked-into); border-left: var(--linked-w) solid var(--linked-line);
}
.linked-notch { position: absolute; left: calc(-1 * var(--linked-w)); z-index: 1; overflow: visible; }
.linked-detail::before { content: ""; position: absolute; top: 0; left: -2px; z-index: 2; width: 3px; height: var(--linked-fade-top); background: linear-gradient(var(--bg), transparent); }
.linked-detail::after { content: ""; position: absolute; left: -2px; right: 0; bottom: 0; z-index: 2; height: var(--linked-fade-y); background: linear-gradient(180deg, transparent, var(--bg) 85%); pointer-events: none; }
.linked-scroll { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-4); padding: 0 0 var(--space-12) var(--space-6); }
.linked-scroll, .linked-cards { scrollbar-width: thin; scrollbar-color: var(--card-line) transparent; }
/* La liste reliée (OffersView, ApplicationsView, RendezVousDesktop) : colonne de 504 px, cartes de 480 px. La barre de
   recherche et de filtres reste en haut, hors de ce qui défile ; seules les cartes défilent dessous (.linked-cards), avec
   une ombre légère sous la barre dès qu'elles ont défilé. La barre de défilement, à gauche (rtl sur .linked-cards, ltr
   sur son contenu, 14 px de marge pour que les cartes restent alignées sur le champ de filtre), commence sous les filtres.
   La carte choisie : fond --linked-selected-bg, contour de 2 px, la flèche à droite. Hors liste reliée (téléphone),
   .linked-cards ne compte pas pour la mise en page. */
.linked-cards { display: contents; }
:is(.offers-grid, .jobs-body, .rdv-grid) > .linked-list {
  --linked-col: 504px; --linked-gap: 24px; --linked-bar: 14px; --linked-room: 3px;
  position: relative; z-index: 2; flex: none; display: flex; flex-direction: column; width: calc(var(--linked-col) + var(--linked-bar)); min-height: 0;
  margin: calc(-1 * var(--linked-room)) 0 0 calc(-1 * var(--linked-bar));
}
.linked-list > .linked-cards { display: block; flex: 1; min-height: 0; overflow-y: auto; direction: rtl; padding: var(--linked-room) var(--linked-gap) var(--space-3) var(--linked-bar); }
.linked-cards > * { direction: ltr; }
.linked-list > [data-linked-tools] { position: relative; z-index: 3; padding: var(--linked-room) var(--linked-gap) calc(var(--space-1) - var(--linked-room)) var(--linked-bar); background: var(--bg); }
.linked-list[data-scrolled] > [data-linked-tools] { box-shadow: 0 10px 12px -12px rgb(27 31 42 / 35%); }
.linked-list .list-card { scroll-margin-block: var(--space-3); }
/* Pas d'enfoncement au clic sur une carte de la liste (comme sur la planche, où seuls les boutons s'enfoncent) : réduite
   de 3 % puis choisie, la carte tremblait. */
.linked-list .list-card:active { transform: none; }
/* Changer de sélection ne change jamais la taille d'une carte (sinon la liste tremble) : la carte choisie garde le trait
   et les marges des autres ; le contour de 2 px de la planche est un outline posé dessus, qui ne prend pas de place
   (remplacé par l'anneau de focus au clavier). */
.linked-list .list-card[aria-current="true"] { --linked-sel: 2px; position: relative; background: var(--linked-selected-bg); box-shadow: none; }
.linked-list .list-card[aria-current="true"]:not(:focus-visible) { outline: var(--linked-sel) solid var(--primary-graphic); outline-offset: calc(-1 * var(--linked-sel)); }
/* La flèche part du bord extérieur de la carte : son décalage tient compte du trait réel de la carte (mesuré, voir
   useLinkedNotch ; Chrome arrondit 1,5 px à 1 px). À 20 px, son trait de 2 px recouvre exactement le contour de 2 px de
   la carte (à 19, les deux traits côte à côte faisaient une marche, le « double trait » signalé par Kevin le 15.11) ; la
   pointe du rail avance d'1 px pour que le contact reste exact. */
.linked-list .list-card-arrow { --linked-arrow: 20px; display: block; position: absolute; top: 50%; right: calc(-1 * (var(--linked-arrow) + var(--linked-card-border))); translate: 0 -50%; overflow: visible; }
</style>
