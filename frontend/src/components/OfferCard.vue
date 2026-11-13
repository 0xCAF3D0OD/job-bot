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

type Chip = { text: string; tone?: "peach" | "blue" | "warn"; title?: string };
const chips = computed<Chip[]>(() => {
  const o = props.offer;
  const out: Chip[] = [];
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
  if (o.status === "later") out.push({ text: "Plus tard" });
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
    :class="{ expired: offer.expired_at && offer.status !== 'applied' }"
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
      >{{ chip.text }}</span>
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
</style>
