<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
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
// A2 (Kevin, 16.11) : écartée sans note, ni anneau ni « Pas encore notée », la pastille neutre « Écartée » ; note
// impossible (trois échecs, ou annonce sans texte), le cercle gris en pointillés et la pastille « Pas de note ».
// Une offre ajoutée à la main est notée même écartée (Kevin, 15.11) : elle garde le cercle d'attente.
const setAside = computed(
  () => unscored.value && !props.offer.added_by_you && (props.offer.status === "filtered_out" || props.offer.status === "ignored"),
);
const noScore = computed(() => unscored.value && !setAside.value && !!props.offer.score_final);
const unratedLabel = computed(() => (noScore.value ? "Pas de note" : "Pas encore notée"));

// Le lien de la carte : la sous-page sur téléphone, ?offre= à côté de la liste sur ordinateur (filtres gardés).
const to = computed(() =>
  phone.value
    ? { path: `${route.path.replace(/\/\d+$/, "")}/${props.offer.id}`, query: route.query }
    : { path: route.path, query: { ...route.query, offre: String(props.offer.id) } },
);

// Une pastille dit une information, jamais qu'elle manque (§11 du 15 novembre, téléphone et ordinateur) : une valeur
// absente ou inconnue ne donne pas de pastille ; l'information reste dans « L'offre en bref » de la fiche.
const UNKNOWN = /^(non (précisée?|indiquée?|renseignée?|communiquée?)|inconnue?|n\/a|-)$/i;
function known(value: string | null | undefined): string | null {
  const text = value?.trim();
  return text && !UNKNOWN.test(text) ? text : null;
}
type Chip = { text: string; tone?: "peach" | "blue" | "warn" | "kept" | "agency"; title?: string };
const chips = computed<Chip[]>(() => {
  const o = props.offer;
  const out: Chip[] = [];
  // Section 35 du 16.11 (CandidaturesOrdinateurAgence, OffreAgence) : « Agence » en premier dans la rangée. Le doute
  // « Employeur caché : annonce d'agence » qu'elle dit déjà ne donne plus, seul, la pastille « À vérifier ».
  const agency = !!o.agency;
  if (agency) out.push({ text: "Agence", tone: "agency", title: "Agence de placement : elle recrute pour un client dont le nom n’est pas donné." });
  const doubts = agency ? o.doubts?.filter((d) => d.kind !== "hidden_employer") : o.doubts;
  // §21 du 15 novembre (ordinateur ; téléphone, Kevin 15.11) : sans note, la pastille neutre « Pas encore notée » en
  // tête (le cercle vide est à droite). Sans profil, « Profil à compléter » le dit à sa place.
  if (setAside.value) out.push({ text: "Écartée" });
  else if (noScore.value) out.push({ text: "Pas de note" });
  else if (unscored.value && !profileEmpty.value) out.push({ text: "Pas encore notée" });
  // « Gardée » (décision de Kevin du 11 novembre : le libellé de l'état `later`, partout), en tête, avec le
  // marque-page orange (planche CandidaturesOrdinateurB du 13.11).
  if (o.status === "later") out.push({ text: "Gardée", tone: "kept" });
  if (o.filter_reasons?.length) out.push({ text: o.filter_reasons[0]!, tone: "warn" });
  else if (doubts?.length)
    out.push({ text: doubts.some((d) => d.kind === "scam") ? "Arnaque possible" : "À vérifier", tone: "warn", title: doubts.map((d) => d.text).join(" ") });
  else if (o.expired_at && o.status !== "applied") out.push({ text: "Retirée", tone: "warn" });
  // Sans profil, aucune offre n'est notée : la puce le dit, au lieu d'un « Pas encore notée » sans fin.
  if (profileEmpty.value && unscored.value && !setAside.value && !noScore.value && !out.length) out.push({ text: "Profil à compléter", tone: "warn", title: "Ajoute ton dernier poste dans Profil pour que jobA1 note les offres." });
  if (!o.description && !o.spontaneous && o.score !== null && o.score !== undefined) out.push({ text: "Provisoire", tone: "peach" });
  const rate = rateText(o.rate_min, o.rate_max);
  if (rate) out.push({ text: rate });
  const contract = known(o.employment_type);
  if (contract) out.push({ text: contract });
  const remote = remoteText(o, phone.value);
  if (remote) out.push({ text: remote });
  if (o.spontaneous) out.push({ text: "Spontanée", tone: "blue" });
  else if (o.added_by_you) out.push({ text: "Ajoutée par toi", tone: "blue" });
  if (props.showDate) out.push({ text: `Reçue ${dateInList(o.first_seen_at)}` });
  return out;
});

// La limite de la formule (docs/125) explique une offre sans note.
const { reached } = usePlan();

// Téléphone (Kevin, 15.11 ; planche Candidatures) : les puces qui ne tiennent pas sur la ligne passent dans « +N »,
// jamais coupées. Mesuré après rendu, et de nouveau quand la carte change de largeur.
const card = ref<{ $el: HTMLElement } | null>(null);
const fits = ref(99);
async function fit(): Promise<void> {
  fits.value = 99;
  if (!phone.value) return;
  await nextTick();
  const box = card.value?.$el.querySelector(".list-card-chips");
  const edge = box?.getBoundingClientRect().right ?? 0;
  while (box && fits.value > 1 && [...box.children].some((c) => c.getBoundingClientRect().right > edge + 0.5)) {
    fits.value = Math.min(fits.value, chips.value.length) - 1;
    await nextTick();
  }
}
let watcher: ResizeObserver | undefined;
onMounted(() => {
  void fit();
  if (typeof ResizeObserver !== "undefined" && card.value) (watcher = new ResizeObserver(() => void fit())).observe(card.value.$el);
});
onUnmounted(() => watcher?.disconnect());
watch([chips, phone], () => void fit());
</script>

<template>
  <ListCard
    ref="card"
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
        v-for="chip in chips.slice(0, fits)"
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
      /></svg><svg
        v-if="chip.tone === 'agency'"
        class="chip-mark"
        :width="phone ? 12 : 14"
        :height="phone ? 12 : 14"
        :stroke-width="phone ? 2.6 : 2.4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
        focusable="false"
      ><path d="M7 7h11l-3-3M17 17H6l3 3" /></svg>{{ chip.text }}</span>
      <span
        v-if="fits < chips.length"
        class="more"
        data-test="offer-chip"
      >+{{ chips.length - fits }}</span>
    </template>
    <template #end>
      <svg
        v-if="unscored && !setAside"
        class="score-ring score-unrated"
        viewBox="0 0 100 100"
        role="img"
        :aria-label="unratedLabel"
        :title="noScore ? 'Pas de note' : profileEmpty || offer.summary_role ? 'Pas de note : ton profil est vide' : reached('score') ? 'Pas encore notée : les offres notées du mois sont utilisées' : 'Pas encore notée, à noter'"
        data-test="score"
      ><circle
        cx="50"
        cy="50"
        r="42"
        fill="none"
        stroke-width="8"
        stroke-dasharray="12 9.99"
      /><path
        d="M38 50H62"
        stroke-width="8"
        stroke-linecap="round"
      /></svg>
      <ScoreRing
        v-else-if="!unscored"
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
/* §21 du 15 novembre (ordinateur 40 px, téléphone 48 px) : sans note, un cercle vide en pointillés et un tiret. */
.score-unrated circle { stroke: var(--linked-line); }
.score-unrated path { stroke: var(--unrated-dash); }
.list-card-chips > .kept { background: var(--peach-soft); color: var(--peach-text); font-weight: var(--weight-bold); }
.chip-mark { flex: none; }
.list-card-chips > .agency { background: var(--agency-bg); color: var(--agency-text); font-weight: var(--weight-bold); }
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
 --offer-19: 19px; --offer-18: 18px; --offer-2: 2px; --offer-3: 3px; --offer-r: 6px;
    grid-template-areas: "logo text end" "chips chips chips"; row-gap: var(--space-2); height: auto;
    padding: var(--offer-19); border: 1px solid var(--line);
  }
  .list-card.list-card-offer[aria-current="true"] { padding: var(--offer-18); }
  .list-card-offer .list-card-text { align-self: center; gap: var(--offer-2); }
  .list-card-offer .list-card-end:has(.score-ring) { align-self: start; justify-self: end; align-items: flex-end; width: auto; margin: calc(-1 * var(--offer-2)) calc(-1 * var(--offer-2)) 0 0; }
  .list-card-offer .list-card-end .score-ring-word { display: none; }
  .list-card-offer .list-card-end .score-ring-wrap { justify-items: end; padding: 0; }
  .list-card-offer > .list-card-chips { margin-top: 0; }
  .list-card-offer > .list-card-chips > * { display: inline-flex; align-items: center; gap: var(--space-1); padding: var(--offer-3) var(--space-2); border-radius: var(--offer-r); line-height: normal; }
  .list-card-offer > .list-card-chips > :not(.peach, .blue, .green, .warn, .kept, .agency) { color: var(--text-lead); }
  .list-card-offer > .list-card-chips > .more { font-weight: var(--weight-bold); }
}
</style>
