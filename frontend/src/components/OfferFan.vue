<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";

import type { Offer } from "../api/client";
import { companyPlace, scoreWord, triageTags } from "../format";
import { buildExcerpt, matchedPassages, offerText, triagePoints } from "../offerPassages";
import { displayTitle } from "../offerTitle";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import ScoreRing from "./ScoreRing.vue";

// L'éventail des offres à trier (maquette du 15 novembre, §12 et §20 ; planches TrierOffresOrdinateurV2, Deux, Une
// et AujourdhuiOrdinateurV2) : jusqu'à 3 cartes de 320 × 430 px, celle du moment devant. 3 offres : −7°, 0°, 7°, les
// hauts alignés ; 2 offres : −4° et +4° ; 1 offre : une carte droite. Couleurs bleu, orange, jaune, les mêmes en clair
// et en sombre.
// - `mini` : l'éventail en petit d'Aujourd'hui (66 %, sans pastilles ni interaction ; le parent nomme le groupe).
// - Sinon (page Trier) : au survol ou au clavier, les cartes s'étalent sur un même plan (340 px d'écart) ; chaque carte
//   se retourne (bouton, aria-pressed) et montre au dos l'extrait surligné, 3 verdicts et « Voir l'annonce complète » ;
//   `kept` : le badge « Gardée ». Le lien du dos est hors du bouton : Entrée l'ouvre sans retourner la carte.
const props = withDefaults(
  defineProps<{ offers: Offer[]; front?: number; mini?: boolean; kept?: number[]; tones?: number[] }>(),
  { front: 0, kept: () => [], tones: () => [] },
);

// Les places de la planche, dans une scène de 1000 px : [gauche, haut, angle, plan]. La première place est celle de
// la carte de devant ; les autres cartes prennent les suivantes dans l'ordre. En petit, la scène ne garde que la
// largeur des cartes, 560 px (220 px de moins à gauche) : l'éventail ne déborde pas de la colonne.
const PLACES: Record<number, [number, number, number, number][]> = {
  1: [[340, 0, 0, 1]],
  2: [[390, 0, 4, 2], [290, 0, -4, 1]],
  3: [[340, 0, 0, 3], [250, 16, -7, 2], [430, 16, 7, 1]],
};
// Étalées : sur un même plan, dans l'ordre, 340 px d'écart, centrées.
const SPREAD: Record<number, number[]> = { 1: [340], 2: [170, 510], 3: [0, 340, 680] };
const TONES = ["fan-blue", "fan-orange", "fan-yellow"] as const;

const flipped = ref<number[]>([]);

// La citation du dos (planche TrierOffresOrdinateurV2, état « dos ») : autant de lignes entières que la carte en laisse
// sous le titre, au-dessus des verdicts et du lien, entre 1 et 5, et « … » à la fin si elle est coupée. Jamais une
// ligne tranchée à mi-hauteur ni un surlignage hors du bloc (Kevin, 19.11.2026). Les tailles de la carte sont fixes :
// le calcul se fait une fois, quand le dos s'affiche, et une seconde fois si la police n'était pas encore chargée.
function fitQuote(el: unknown): void {
  if (!(el instanceof HTMLElement) || el.dataset.lines) return;
  const back = el.parentElement;
  if (!back?.clientHeight) return;
  const gap = parseFloat(getComputedStyle(back).rowGap) || 0;
  let room = back.clientHeight - gap * (back.children.length - 1);
  for (const child of back.children) if (child !== el) room -= (child as HTMLElement).offsetHeight;
  const quote = getComputedStyle(el);
  const line = parseFloat(quote.lineHeight);
  const lines = Math.min(5, Math.max(1, Math.floor((room - parseFloat(quote.paddingTop) - parseFloat(quote.paddingBottom)) / line)));
  el.style.setProperty("--lines", String(lines));
  el.dataset.lines = String(lines);
  if (document.fonts && document.fonts.status !== "loaded") {
    void document.fonts.ready.then(() => {
      delete el.dataset.lines;
      el.style.removeProperty("--lines");
      fitQuote(el);
    });
  }
}
const root = ref<HTMLElement | null>(null);
function fitQuotes(): void {
  root.value?.querySelectorAll(".fan-quote").forEach(fitQuote);
}
watch(flipped, () => void nextTick(fitQuotes));
onMounted(fitQuotes);
function flip(id: number): void {
  flipped.value = flipped.value.includes(id) ? flipped.value.filter((f) => f !== id) : [...flipped.value, id];
}

const cards = computed(() => {
  const shown = props.offers.slice(0, 3);
  const n = shown.length;
  const places = PLACES[n] ?? [];
  const front = Math.min(props.front, n - 1);
  // L'ordre des places : la carte de devant d'abord, puis les autres dans l'ordre de la pile.
  const order = [front, ...shown.map((_, i) => i).filter((i) => i !== front)];
  const shift = props.mini ? 220 : 0;
  return shown.map((offer, i) => {
    const [left, top, angle, plane] = places[order.indexOf(i)] ?? [0, 0, 0, 0];
    // Les notes manuscrites : deux points retrouvés et au plus un point à vérifier ; chacune sur 1 ligne, puis
    // des points de suspension (Kevin, 16.11) ; la note entière dans l'aria-label.
    const points = triagePoints(offer);
    const score = offer.score == null ? null : Math.round(offer.score);
    const company = offer.company || "Entreprise non indiquée";
    const text = props.mini ? "" : offerText(offer);
    return {
      offer,
      tone: TONES[(props.tones?.[i] ?? i) % 3],
      style: {
        "--x": `${left - shift}px`,
        "--y": `${top}px`,
        "--r": `${angle}deg`,
        "--sx": `${SPREAD[n]?.[i] ?? left}px`,
        zIndex: plane,
      },
      // La forme courte de l'IA (score-v9) si elle tient en 28 caractères, sinon le texte complet, coupé à 1 ligne
      // (Kevin, 15.11 : forme courte absente, vide ou trop longue).
      notes: points.map((p) => (p.short && p.short.length < 29 ? p.short : p.text)),
      points,
      score,
      company,
      place: companyPlace(company, offer.location, true),
      // Les pastilles en capitales : contrat, taux, télétravail, puis le mot de la note.
      tags: props.mini
        ? []
        : [...triageTags(offer), ...(score == null ? [] : [scoreWord(score).word])].slice(0, 4),
      excerpt: text ? buildExcerpt(text, matchedPassages(offer), 160) : null,
      // Le nom du bouton qui retourne la carte : poste, entreprise, les notes entières (affichées sur 1 ligne).
      label: [`${displayTitle(offer.title, offer)}, ${company}`, ...points.map((p) => p.text.replace(/[.\s]+$/, "")), "Retourner pour voir l’extrait"].join(". "),
      front: i === front,
      turned: flipped.value.includes(offer.id),
      kept: props.kept.includes(offer.id),
    };
  });
});
</script>

<template>
  <div
    ref="root"
    :class="['fan', mini ? 'fan-mini' : 'fan-live']"
    data-test="offer-fan"
  >
    <div class="fan-stage">
      <div
        v-for="card in cards"
        :key="card.offer.id"
        :class="['fan-card', card.tone, { 'fan-front': card.front, 'fan-turned': card.turned }]"
        :style="card.style"
        :aria-hidden="mini ? 'true' : undefined"
        data-test="fan-card"
      >
        <button
          v-if="!mini"
          type="button"
          class="fan-flip"
          :aria-pressed="card.turned ? 'true' : 'false'"
          :aria-label="card.label"
          data-test="fan-flip"
          @click="flip(card.offer.id)"
        />
        <template v-if="!card.turned">
          <div class="fan-top">
            <CompanyLogo
              :offer="card.offer"
              pair
              class="fan-logo"
            />
            <ScoreRing
              :score="card.score"
              bare
            />
          </div>
          <div class="fan-notes">
            <p>
              <span
                v-for="(note, i) in card.notes"
                :key="i"
              >{{ note }}</span>
            </p>
          </div>
          <div class="fan-names">
            <b>{{ displayTitle(card.offer.title, card.offer) }}</b>
            <span>{{ card.place }}</span>
          </div>
          <div
            v-if="card.tags.length"
            class="fan-tags"
            data-test="fan-tags"
          >
            <span
              v-for="tag in card.tags"
              :key="tag"
            >{{ tag }}</span>
          </div>
        </template>
        <div
          v-else
          class="fan-back"
          data-test="fan-back"
        >
          <p class="fan-back-head">
            <b>{{ displayTitle(card.offer.title, card.offer) }}</b><span>{{ card.company }}</span>
          </p>
          <p
            v-if="card.excerpt"
            class="fan-quote"
            data-test="fan-quote"
          >
            <span class="fan-quote-text">«&nbsp;<template
              v-for="(part, i) in card.excerpt.segments"
              :key="i"
            >
              <mark v-if="part.mark">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
            </template>&nbsp;»</span>
          </p>
          <ul class="fan-verdicts">
            <li
              v-for="point in card.points"
              :key="point.text"
            >
              <i
                :class="{ ok: point.ok }"
                aria-hidden="true"
              ><AppIcon
                v-if="point.ok"
                name="tick"
              /><template v-else>?</template></i>
              <span><span class="visually-hidden">{{ point.ok ? "Retrouvé : " : "À vérifier : " }}</span>{{ point.text }}</span>
            </li>
          </ul>
          <RouterLink
            :to="{ path: '/candidatures/offres', query: { offre: card.offer.id } }"
            class="fan-read"
            data-test="fan-read"
          >
            Voir l’annonce complète<svg
              class="fan-arrow"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              aria-hidden="true"
            ><path d="M3 9 9 3M4 3h5v5" /></svg>
          </RouterLink>
        </div>
        <span
          v-if="card.kept"
          class="fan-kept"
          data-test="fan-kept"
        ><svg
          width="9"
          height="12"
          viewBox="0 0 12 15"
          aria-hidden="true"
        ><path
          d="M1 1.5A1.5 1.5 0 0 1 2.5 0h7A1.5 1.5 0 0 1 11 1.5V15L6 11.5 1 15z"
          fill="#F2853A"
        /></svg>Gardée</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Les valeurs des planches, en pixels de la scène (l'éventail en petit les réduit toutes par scale). Ramenés à la
   grille de 4 : haut de la carte et écart des notes 22 px (24), écart de l'entreprise en petit 6 px (4), pastilles
   6 / 11 (4 / 12), écart des pastilles 6 (8), marges du dos 14 / 10 (16 / 12). Gardés tels que dessinés (tailles de
   texte et rayons, pas des espacements) : rayon 26, notes 22 / 26, titre 26 / 30. */
.fan { --fan-r: 26px; --fan-14: 14px; --fan-22: 22px; --fan-26: 26px; --fan-30: 30px; --fan-place: 15px; --fan-place-lh: 21px; position: relative; height: 470px; }
.fan-stage { position: absolute; left: 50%; width: 1000px; height: 100%; transform: translateX(-50%); }
/* §20 : 66 %, origine en haut au centre, bloc de 318 px ; l'entreprise écrite à 20 px (13 px affichés). */
.fan-mini { --fan-place: 20px; --fan-place-lh: var(--fan-26); height: 318px; }
.fan-mini .fan-stage { width: 560px; height: 470px; transform: translateX(-50%) scale(0.66); transform-origin: 50% 0; }
.fan-card { position: absolute; left: var(--x); top: var(--y); display: flex; flex-direction: column; box-sizing: border-box; width: 320px; height: 430px; padding: var(--space-6); border-radius: var(--fan-r); background: var(--fan-bg); color: var(--fan-ink); transform: rotate(var(--r)); transform-origin: 50% 100%; box-shadow: 0 18px 40px rgb(27 31 42 / 18%); }
.fan-blue { --fan-bg: var(--primary); --fan-ink: var(--on-primary); --fan-chip: rgb(255 255 255 / 18%); }
.fan-orange { --fan-bg: var(--fan-orange); --fan-ink: var(--on-peach); }
.fan-yellow { --fan-bg: var(--fan-yellow); --fan-ink: var(--on-peach); }
.fan-top { display: flex; justify-content: space-between; }
.fan .fan-logo { width: 48px; height: 48px; border-radius: var(--fan-14); font-size: var(--font-label); font-weight: var(--weight-heavy); }
.fan .fan-logo:not(.image) { background: rgb(0 0 0 / 18%); color: inherit; }
/* L'anneau de note (ScoreRing) aux couleurs de la carte : piste sombre translucide, arc et chiffre dans l'encre de la
   carte, graduations dans sa couleur de fond, 56 px. */
/* La classe globale « .close » (bouton de fermeture) porte le même nom que la note « Proche » : marges remises à 0. */
.fan :deep(.score-ring-wrap) { padding: 0; }
.fan :deep(circle) { stroke-width: 10; }
.fan :deep(.score-ring) { --ring: var(--fan-ink); --ring-soft: rgb(0 0 0 / 14%); --ring-gap: var(--fan-bg); width: 56px; height: 56px; padding: 0; font-size: var(--font-title); font-weight: var(--weight-heavy); }
/* 24 px au moins entre la dernière note et le poste, comme entre l'en-tête et les notes (Kevin, 16.11.2026). */
.fan-notes { flex: auto; min-height: 0; margin-block: var(--space-6); font: var(--fan-22) / var(--fan-26) var(--font-hand); letter-spacing: 0.02em; opacity: 0.85; }
/* Une hauteur en lignes entières : une note qui ne tient pas est coupée entre deux lignes, jamais au milieu. */
.fan-notes p { max-height: round(down, 100%, var(--fan-26)); margin: 0; overflow: hidden; }
/* Une ligne par note, « … » si elle ne tient pas, forme courte ou non (Kevin, 16.11.2026). */
.fan-notes span, .fan-names span { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
/* Une note coupée garde une marge de chaque côté, comme une note courte : environ 88 % de la largeur, centrée
   (Kevin, 16.11) ; 16 px de chaque côté plutôt que 88 %, pour rester sur la grille de 4 (240 px sur 272). */
.fan-notes span { margin-inline: var(--space-4); }
.fan-names b { display: -webkit-box; font-size: var(--fan-26); line-height: var(--fan-30); letter-spacing: -0.3px; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.fan-names span { margin-top: var(--space-1); font-size: var(--fan-place); line-height: var(--fan-place-lh); opacity: 0.9; }

/* La page Trier : étalement, retournement, pastilles, badge. Le survol se lit sur la largeur des cartes étalées. */
.fan-live { width: 1000px; margin-inline: auto; }
.fan-live .fan-card { transition: 0.35s cubic-bezier(0.2, 0.8, 0.2, 1); transition-property: left, top, transform; }
.fan-live:is(:hover, :focus-within) .fan-card { left: var(--sx); top: 0; transform: none; }
.fan-flip { position: absolute; inset: 0; z-index: 1; padding: 0; border: 0; border-radius: inherit; background: none; cursor: pointer; }
.fan-flip:focus-visible { outline: 2px solid var(--primary-graphic); outline-offset: 3px; }
.fan-turned > :not(.fan-flip, .fan-kept) { animation: fan-turn 0.3s ease-out; }
@keyframes fan-turn { from { transform: perspective(900px) rotateY(80deg); opacity: 0; } }
.fan-tags { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-4); }
.fan-tags span { padding: var(--space-1) var(--space-3); border-radius: var(--radius-sm); background: var(--fan-chip, rgb(27 31 42 / 12%)); font-size: var(--font-caption); font-weight: var(--weight-bold); letter-spacing: 0.03em; text-transform: uppercase; white-space: nowrap; }
.fan-back { display: flex; flex-direction: column; gap: var(--space-4); height: 100%; text-align: left; }
.fan-back-head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-3); margin: 0; font-size: var(--font-body); }
.fan-back-head span { font-size: var(--font-small); opacity: 0.8; white-space: nowrap; }
/* La citation ne rétrécit pas avec la carte (sinon une ligne est tranchée) : elle garde --lines lignes entières
   (fitQuote, sur .fan-quote-text), centrée comme sur la planche ; le surlignage, 2 px de chaque côté, reste dans le bloc. */
.fan-quote { flex: none; margin: 0; text-align: center; padding: var(--space-3) var(--space-4); border-radius: var(--fan-14); background: rgb(255 255 255 / 55%); color: var(--on-peach); font-size: var(--font-label); line-height: var(--fan-22); }
/* La coupe se fait sur le texte, pas sur le bloc : la marge du bas ne laisse jamais voir le haut de la ligne suivante. */
.fan-quote-text { display: -webkit-box; -webkit-line-clamp: var(--lines, 5); line-clamp: var(--lines, 5); -webkit-box-orient: vertical; overflow: hidden; overflow-wrap: anywhere; }
.fan-quote mark { padding: 0 calc(var(--space-1) / 2); border-radius: var(--radius-sm); background: var(--fan-yellow); color: inherit; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.fan-verdicts { display: grid; gap: var(--space-3); margin: 0; padding: 0; list-style: none; font-size: var(--font-label); line-height: var(--fan-22); }
.fan-verdicts li { display: flex; gap: var(--space-3); align-items: flex-start; }
/* Un verdict très long s'arrête à 3 lignes entières, « … » à la fin : le lien reste dans la carte. */
.fan-verdicts li > span { display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.fan-verdicts i { flex: none; display: grid; place-items: center; width: 22px; height: 22px; border-radius: var(--radius-pill); background: rgb(0 0 0 / 14%); font-style: normal; font-weight: var(--weight-heavy); font-size: var(--font-caption); }
.fan-verdicts i.ok { background: var(--fan-ink); color: var(--fan-bg); }
.fan-verdicts :deep(svg) { width: var(--font-caption); height: var(--font-caption); stroke-width: 3; }
.fan-read { position: relative; z-index: 2; margin-top: auto; align-self: flex-start; font-size: var(--font-label); font-weight: var(--weight-bold); color: inherit; text-decoration: none; }
.fan-read:hover { color: inherit; text-decoration: underline; }
/* La flèche du lien (Kevin, 15.11) : une icône, pas le caractère « ↗ » absent de la police ; 0,8 em, 2 px après le texte. */
.fan-arrow { width: 0.8em; height: 0.8em; margin-left: calc(var(--space-1) / 2); }
/* Étalées, la carte du moment est entourée (planche, état « Gardée » et dos). */
.fan-live:is(:hover, :focus-within) .fan-front { outline: 3px solid var(--text); outline-offset: 4px; }
.fan-kept { position: absolute; right: var(--space-5); top: calc(-1 * var(--space-3)); z-index: 2; display: inline-flex; align-items: center; gap: var(--space-1); padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); background: var(--peach-soft); color: var(--peach-text); font-size: var(--font-caption); font-weight: var(--weight-bold); }
@media (prefers-reduced-motion: reduce) {
  .fan-live .fan-card { transition: none; }
  .fan-turned > :not(.fan-flip, .fan-kept) { animation: fan-fade 0.15s linear; }
  @keyframes fan-fade { from { opacity: 0; } }
}
</style>
