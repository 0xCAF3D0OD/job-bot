<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { companyPlace } from "../format";
import CompanyLogo from "./CompanyLogo.vue";

// L'éventail des offres à trier (maquette du 15 novembre, §12 et §20 ; planches TrierOffresOrdinateurV2, Deux, Une
// et AujourdhuiOrdinateurV2) : jusqu'à 3 cartes de 320 × 430 px, la meilleure devant. 3 offres : −7°, 0°, 7°, les
// hauts alignés ; 2 offres : −4° et +4° ; 1 offre : une carte droite. Couleurs par rang : bleu, orange, jaune, les
// mêmes en clair et en sombre. `mini` : l'éventail en petit d'Aujourd'hui (66 %, sans interaction).
// Les cartes sont décoratives : le parent nomme le groupe (aria-label) et porte les boutons.
const props = defineProps<{ offers: Offer[]; mini?: boolean }>();

// Les places de la planche (scène de 1000 px), ramenées à la largeur des cartes, 560 px (la planche moins 220 px à
// gauche) : l'éventail reste centré et ne déborde pas de la page. [gauche, haut, angle, plan].
const PLACES: Record<number, [number, number, number, number][]> = {
  1: [[120, 0, 0, 1]],
  2: [[170, 0, 4, 2], [70, 0, -4, 1]],
  3: [[120, 0, 0, 3], [30, 16, -7, 2], [210, 16, 7, 1]],
};
const TONES = ["fan-blue", "fan-orange", "fan-yellow"] as const;
// L'anneau de note de la planche : rayon 42, circonférence 263,89.
const RING = 263.89;

const cards = computed(() => {
  const shown = props.offers.slice(0, 3);
  const places = PLACES[shown.length] ?? [];
  return shown.map((offer, rank) => {
    const [left, top, angle, plane] = places[rank] ?? [0, 0, 0, 0];
    // Les notes manuscrites : deux points retrouvés et au plus un point à vérifier, comme sur la page Trier ; d'un
    // point « Kubernetes : plateforme de 40 nœuds », la carte ne garde que « Kubernetes » (notes courtes de la planche).
    const check = offer.gaps?.[0]?.text;
    const notes = [...(offer.strengths ?? []).slice(0, check ? 2 : 3).map((s) => s.text), ...(check ? [check] : [])].map(
      (text) => text.split(" : ")[0],
    );
    return {
      offer,
      tone: TONES[rank],
      style: { left: `${left}px`, top: `${top}px`, zIndex: plane, transform: `rotate(${angle}deg)` },
      notes,
      score: offer.score == null ? null : Math.round(offer.score),
      place: companyPlace(offer.company || "Entreprise non indiquée", offer.location, true),
    };
  });
});
</script>

<template>
  <div
    :class="['fan', { 'fan-mini': mini }]"
    data-test="offer-fan"
  >
    <div class="fan-stage">
      <div
        v-for="card in cards"
        :key="card.offer.id"
        :class="['fan-card', card.tone]"
        :style="card.style"
        aria-hidden="true"
        data-test="fan-card"
      >
        <div class="fan-top">
          <CompanyLogo
            :offer="card.offer"
            pair
            class="fan-logo"
          />
          <svg
            class="fan-ring"
            viewBox="0 0 100 100"
            fill="none"
            stroke-width="10"
          >
            <circle
              cx="50"
              cy="50"
              r="42"
              stroke="#000"
              stroke-opacity=".14"
            />
            <circle
              v-if="card.score != null"
              cx="50"
              cy="50"
              r="42"
              stroke="currentColor"
              :stroke-dasharray="`${((card.score / 100) * RING).toFixed(2)} ${RING}`"
              transform="rotate(-90 50 50)"
            />
            <path
              d="M50 1V15M85 50H99M50 85V99M1 50H15"
              stroke-width="3.5"
            />
            <text
              x="50"
              y="62"
              text-anchor="middle"
              fill="currentColor"
              font-size="32"
              font-weight="800"
            >{{ card.score ?? "?" }}</text>
          </svg>
        </div>
        <div class="fan-notes">
          <span
            v-for="(note, i) in card.notes"
            :key="i"
          >{{ note }}</span>
        </div>
        <div class="fan-names">
          <b>{{ card.offer.title }}</b>
          <span>{{ card.place }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Les valeurs des planches, en pixels de la scène (l'éventail en petit les réduit toutes par scale). Ramenés à la
   grille de 4 : haut de la carte et écart des notes 22 px (24), écart de l'entreprise en petit 6 px (4). Gardés tels
   que dessinés (tailles de texte et rayon, pas des espacements) : rayon 26, notes 22 / 26, titre 26 / 30. */
.fan { --fan-r: 26px; --fan-14: 14px; --fan-22: 22px; --fan-26: 26px; --fan-30: 30px; --fan-place: 15px; --fan-place-lh: 21px; position: relative; height: 470px; }
.fan-stage { position: absolute; left: 50%; width: 560px; height: 100%; transform: translateX(-50%); }
/* §20 : 66 %, origine en haut au centre, bloc de 318 px ; l'entreprise écrite à 20 px (13 px affichés). */
.fan-mini { --fan-place: 20px; --fan-place-lh: var(--fan-26); height: 318px; }
.fan-mini .fan-stage { height: 470px; transform: translateX(-50%) scale(0.66); transform-origin: 50% 0; }
.fan-card { position: absolute; display: flex; flex-direction: column; box-sizing: border-box; width: 320px; height: 430px; padding: var(--space-6); border-radius: var(--fan-r); background: var(--fan-bg); color: var(--fan-ink); transform-origin: 50% 100%; box-shadow: 0 18px 40px rgb(27 31 42 / 18%); }
.fan-blue { --fan-bg: var(--primary); --fan-ink: var(--on-primary); }
.fan-orange { --fan-bg: var(--fan-orange); --fan-ink: var(--on-peach); }
.fan-yellow { --fan-bg: var(--fan-yellow); --fan-ink: var(--on-peach); }
.fan-top { display: flex; justify-content: space-between; }
.fan .fan-logo { width: 48px; height: 48px; border-radius: var(--fan-14); font-size: var(--font-label); font-weight: var(--weight-heavy); }
.fan .fan-logo:not(.image) { background: rgb(0 0 0 / 18%); color: inherit; }
.fan-ring { width: 56px; height: 56px; }
.fan-ring path { stroke: var(--fan-bg); }
.fan-notes { flex: auto; overflow: hidden; margin-top: var(--space-6); font: var(--fan-22) / var(--fan-26) var(--font-hand); letter-spacing: 0.02em; opacity: 0.85; }
.fan-notes span, .fan-names span { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.fan-names b { display: -webkit-box; font-size: var(--fan-26); line-height: var(--fan-30); letter-spacing: -0.3px; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.fan-names span { margin-top: var(--space-1); font-size: var(--fan-place); line-height: var(--fan-place-lh); opacity: 0.9; }
</style>
