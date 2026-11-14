<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import type { Offer } from "../api/client";
import { dateInList } from "../dates";
import { rateText, remoteText } from "../format";
import ListCard from "./ListCard.vue";
import ScoreRing from "./ScoreRing.vue";
import { usePlan } from "../composables/usePlan";
import { useProfileEmpty } from "../composables/useProfileEmpty";
import { usePhone } from "../composables/usePhone";

// Une offre dans À traiter (maquettes CandidaturesOrdinateur et Candidatures, 7.11.2026) : la carte de liste
// commune, avec l'anneau et son mot à droite. Ce qui demande attention (écartée, à vérifier, retirée) et la note
// provisoire deviennent des puces ; rien d'autre n'entre dans la carte (ni « Préparer », ni « ⋯ », ni ligne
// « Il te manque » : la fiche les a). La date n'y est que hors du tri « Par jour », où le titre du jour la donne.
const props = defineProps<{ offer: Offer; selected: boolean; showDate?: boolean }>();
defineEmits<{ select: [] }>();
const { phone } = usePhone();
const route = useRoute();
const { empty: profileEmpty } = useProfileEmpty();
const unscored = computed(() => props.offer.score === null || props.offer.score === undefined);

// Le lien de la carte : la sous-page sur téléphone, ?offre= à côté de la liste sur ordinateur (filtres gardés).
const to = computed(() =>
  phone.value
    ? { path: `${route.path.replace(/\/\d+$/, "")}/${props.offer.id}`, query: route.query }
    : { path: route.path, query: { ...route.query, offre: String(props.offer.id) } },
);

type Chip = { text: string; tone?: "peach" | "blue" | "warn" | "kept"; title?: string };
const chips = computed<Chip[]>(() => {
  const o = props.offer;
  const out: Chip[] = [];
  // « Gardée » (décision de Kevin du 11 novembre : le libellé de l'état `later`, partout), en tête, avec le
  // marque-page orange (planche CandidaturesOrdinateurB du 13.11).
  if (o.status === "later") out.push({ text: "Gardée", tone: "kept" });
  if (o.filter_reasons?.length) out.push({ text: o.filter_reasons[0]!, tone: "warn" });
  else if (o.doubts?.length)
    out.push({ text: o.doubts.some((d) => d.kind === "scam") ? "Arnaque possible" : "À vérifier", tone: "warn", title: o.doubts.map((d) => d.text).join(" ") });
  else if (o.expired_at && o.status !== "applied") out.push({ text: "Retirée", tone: "warn" });
  // Sans profil, aucune offre n'est notée : la puce le dit, au lieu d'un « Pas encore notée » sans fin.
  if (profileEmpty.value && unscored.value && !out.length) out.push({ text: "Profil à compléter", tone: "warn", title: "Ajoute ton dernier poste dans Profil pour que jobA1 note les offres." });
  if (!o.description && !o.spontaneous && o.score !== null && o.score !== undefined) out.push({ text: "Provisoire", tone: "peach" });
  const rate = rateText(o.rate_min, o.rate_max);
  if (rate) out.push({ text: rate });
  out.push({ text: o.employment_type || "Contrat non précisé" });
  const remote = remoteText(o, phone.value);
  if (remote) out.push({ text: remote });
  if (o.spontaneous) out.push({ text: "Spontanée", tone: "blue" });
  else if (o.added_by_you) out.push({ text: "Ajoutée par toi", tone: "blue" });
  if (props.showDate) out.push({ text: `Reçue ${dateInList(o.first_seen_at)}` });
  return out;
});

// La limite de la formule (docs/125) explique une offre sans note.
const { reached } = usePlan();
</script>

<template>
  <ListCard
    :title="offer.title"
    :company="offer.company ?? 'Entreprise non indiquée'"
    :location="offer.location"
    :logo="offer.has_logo ? `/api/offers/${offer.id}/logo` : null"
    :to="to"
    :selected="selected"
    :class="['list-card-offer', { expired: offer.expired_at && offer.status !== 'applied' }]"
    data-test="offer"
    @select="$emit('select')"
  >
    <template #chips>
      <span
        v-for="chip in chips"
        :key="chip.text"
        :class="chip.tone"
        :title="chip.title"
        data-test="offer-chip"
      ><svg
        v-if="chip.tone === 'kept'"
        class="chip-mark"
        width="9"
        height="12"
        viewBox="0 0 12 15"
        aria-hidden="true"
        focusable="false"
      ><path
        d="M1 1.5A1.5 1.5 0 0 1 2.5 0h7A1.5 1.5 0 0 1 11 1.5V15L6 11.5 1 15z"
        fill="#F2853A"
      /></svg>{{ chip.text }}</span>
    </template>
    <template #end>
      <ScoreRing
        worded
        :score="offer.score ?? null"
        :pending="profileEmpty || offer.summary_role ? 'Pas de note : ton profil est vide' : reached('score') ? 'Pas encore notée : les offres notées du mois sont utilisées' : 'Pas encore notée, à noter'"
        :stale="offer.score_stale"
      />
    </template>
  </ListCard>
</template>

<style>
/* L'anneau de 48 px et son mot en 12 px gras (maquette) ; sans note, « Pas encore notée » sur deux lignes. */
.list-card-end .score-ring { width: 3rem; height: 3rem; font-size: var(--font-body); }
.list-card-end .score-ring-worded { gap: var(--card-2); }
/* Du texte : le gris secondaire (6,3:1 sur la carte), jamais --faint, réservé à ce qui n’est pas du texte. */
.list-card-end .score-pending { font-weight: var(--weight-bold); color: var(--text-secondary); }
.list-card.expired { opacity: 0.6; }
.list-card-chips > .kept { background: var(--peach-soft); color: var(--peach-text); font-weight: var(--weight-bold); }
.chip-mark { flex: none; }
/* Ordinateur, maquette du 14 novembre (§1 ; CandidaturesOrdinateurB) : l'anneau de 40 px en haut à droite, sans son
   mot (il reste dans le nom de l'anneau, « Proche : 92 sur 100 », et dans la fiche) ; même marge de 16 px en haut et
   à droite (ListCard). Les séparations prennent le fond de la carte, bleu pâle quand elle est choisie. */
@media (min-width: 1024px) {
  .list-card-end .score-ring { width: 2.5rem; height: 2.5rem; }
  .list-card-end:has(.score-ring) { align-self: start; width: auto; }
  .list-card-end .score-ring-word { display: none; }
  .list-card[aria-current="true"] { --ring-gap: var(--selected-bg); }
}
/* Téléphone, maquette du 14 novembre (Candidatures, §1) : logo, poste et « entreprise · lieu », l'anneau de 48 px en haut à
   droite sans son mot (il reste dans le nom de l'anneau et dans la fiche), à 20 px du haut et de la droite comme de la
   gauche (marge de 20 px, trait de 1 px --line) ; les puces sur toute la largeur dessous, à 8 px, 6 px entre elles. */
@media (max-width: 820px) {
  .list-card.list-card-offer {
    --offer-20: 20px; --offer-19: 19px; --offer-18: 18px; --offer-8: 8px; --offer-2: 2px; --offer-3: 3px; --offer-r: 6px;
    grid-template-areas: "logo text end" "chips chips chips"; row-gap: var(--offer-8); height: auto;
    padding: var(--offer-19); border: 1px solid var(--line);
  }
  .list-card.list-card-offer[aria-current="true"] { padding: var(--offer-18); }
  .list-card-offer .list-card-text { align-self: center; gap: var(--offer-2); }
  .list-card-offer .list-card-end:has(.score-ring) { align-self: start; justify-self: end; align-items: flex-end; width: auto; margin: calc(-1 * var(--offer-2)) calc(-1 * var(--offer-2)) 0 0; }
  .list-card-offer .list-card-end .score-ring-word { display: none; }
  .list-card-offer .list-card-end .score-ring-wrap { justify-items: end; padding: 0; }
  .list-card-offer > .list-card-chips { margin-top: 0; }
  .list-card-offer > .list-card-chips > * { display: inline-flex; align-items: center; gap: var(--space-1); padding: var(--offer-3) var(--offer-8); border-radius: var(--offer-r); line-height: normal; }
  .list-card-offer > .list-card-chips > :not(.peach, .blue, .green, .warn, .kept) { color: var(--text-lead); }
}
</style>
