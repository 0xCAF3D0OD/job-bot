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

// Les places de la planche, dans une scène de 1000 × 470 px : [gauche, haut, angle, plan].
const PLACES: Record<number, [number, number, number, number][]> = {
  1: [[340, 0, 0, 1]],
  2: [[390, 0, 4, 2], [290, 0, -4, 1]],
  3: [[340, 0, 0, 3], [250, 16, -7, 2], [430, 16, 7, 1]],
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
          >
            <circle
              cx="50"
              cy="50"
              r="42"
              class="fan-ring-track"
            />
            <circle
              v-if="card.score != null"
              cx="50"
              cy="50"
              r="42"
              class="fan-ring-arc"
              :stroke-dasharray="`${((card.score / 100) * RING).toFixed(2)} ${RING}`"
              transform="rotate(-90 50 50)"
            />
            <path
              d="M50 1V15M85 50H99M50 85V99M1 50H15"
              class="fan-ring-ticks"
            />
            <text
              x="50"
              y="62"
              text-anchor="middle"
            >{{ card.score ?? "?" }}</text>
          </svg>
        </div>
        <div
          v-if="card.notes.length"
          class="fan-notes"
        >
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
/* Les valeurs des planches, en pixels de la scène (l'éventail en petit les réduit toutes par scale). Hors grille de 4,
   gardés tels que dessinés parce qu'ils sont réduits à 66 % : rayon 26, marges 22 / 26 / 30, notes 22 / 26. */
.fan {
  --fan-w: 320px; --fan-h: 430px; --fan-stage-w: 1000px; --fan-stage-h: 470px; --fan-r: 26px; --fan-logo: 48px; --fan-logo-r: 14px;
  --fan-ring: 56px; --fan-note: 22px; --fan-note-lh: 26px; --fan-title: 26px; --fan-title-lh: 30px; --fan-place: 15px; --fan-place-lh: 21px; --fan-22: 22px; --fan-6: 6px; --fan-score: 32px;
  --fan-chip: rgb(0 0 0 / 18%); --fan-track: rgb(0 0 0 / 14%); --fan-shadow: 0 18px 40px rgb(27 31 42 / 18%);
  position: relative; height: var(--fan-stage-h);
}
.fan-stage { position: absolute; left: 50%; top: 0; width: var(--fan-stage-w); height: var(--fan-stage-h); transform: translateX(-50%); }
/* §20 : 66 %, origine en haut au centre, bloc de 318 px ; l'entreprise écrite à 20 px (13 px affichés). */
.fan-mini { --fan-place: 20px; --fan-place-lh: 26px; height: 318px; }
.fan-mini .fan-stage { transform: translateX(-50%) scale(0.66); transform-origin: 50% 0; }
.fan-card {
  position: absolute; display: flex; flex-direction: column; box-sizing: border-box; width: var(--fan-w); height: var(--fan-h);
  padding: var(--fan-22) var(--space-6) var(--space-6); border-radius: var(--fan-r); background: var(--fan-bg); color: var(--fan-ink);
  transform-origin: 50% 100%; box-shadow: var(--fan-shadow); text-align: start;
}
.fan-blue { --fan-bg: var(--primary); --fan-ink: var(--on-primary); }
.fan-orange { --fan-bg: var(--fan-orange); --fan-ink: var(--on-peach); }
.fan-yellow { --fan-bg: var(--fan-yellow); --fan-ink: var(--on-peach); }
.fan-top { display: flex; justify-content: space-between; align-items: flex-start; }
.fan-logo { width: var(--fan-logo); height: var(--fan-logo); border-radius: var(--fan-logo-r); font-size: var(--font-label); font-weight: var(--weight-heavy); }
.fan .fan-card .fan-logo:not(.image) { background: var(--fan-chip); color: var(--fan-ink); }
.fan-ring { flex: none; width: var(--fan-ring); height: var(--fan-ring); }
.fan-ring circle { fill: none; stroke-width: 10; }
.fan-ring-track { stroke: var(--fan-track); }
.fan-ring-arc { stroke: var(--fan-ink); }
.fan-ring-ticks { stroke: var(--fan-bg); stroke-width: 3.5; }
.fan-ring text { fill: var(--fan-ink); font-family: inherit; font-size: var(--fan-score); font-weight: var(--weight-heavy); }
.fan-notes { margin-top: var(--fan-22); font-family: var(--font-hand); font-size: var(--fan-note); line-height: var(--fan-note-lh); letter-spacing: 0.02em; opacity: 0.85; }
.fan-notes span { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.fan-names { margin-top: auto; }
.fan-names b { display: -webkit-box; font-size: var(--fan-title); line-height: var(--fan-title-lh); letter-spacing: -0.3px; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.fan-names span { display: block; margin-top: var(--space-1); font-size: var(--fan-place); line-height: var(--fan-place-lh); opacity: 0.9; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.fan-mini .fan-names span { margin-top: var(--fan-6); }
</style>
