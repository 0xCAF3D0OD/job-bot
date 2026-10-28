<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import type { Offer } from "../api/client";
import { dateInList } from "../dates";
import OfferLine from "./OfferLine.vue";
import ScoreWord from "./ScoreWord.vue";
import StatusPill from "./StatusPill.vue";
import { usePlan } from "../composables/usePlan";

// Une offre dans la liste d'Offres : la Ligne d'offre complète (planche « Ligne d'offre », 1.6.7x) ;
// le détail s'ouvre à droite. Toute la ligne sélectionne l'offre ; pas de mot d'action sur une offre
// nouvelle (choix de Kevin), « Préparer » seulement sur une offre gardée. La date n'y est que hors du
// tri « Par jour », où la ligne du jour la donne.
const props = defineProps<{ offer: Offer; selected: boolean; showDate?: boolean }>();
defineEmits<{ select: [] }>();
const router = useRouter();

const expired = computed(() => Boolean(props.offer.expired_at) && props.offer.status !== "applied");
// Une seule ligne sous le lieu, la plus utile pour décider : écartée, douteuse, retirée, puis ce qui
// manque (en gris : il explique la note ; l'orange dit d'agir, docs/121 §C.5).
const alert = computed<{ text: string; kind: "warn" | "danger" | "gap" } | null>(() => {
  const o = props.offer;
  if (o.filter_reasons?.length) return { text: o.filter_reasons[0]!, kind: "warn" };
  if (o.doubts?.length) {
    const scam = o.doubts.some((d) => d.kind === "scam");
    return { text: scam ? "Arnaque possible" : "À vérifier", kind: "danger" };
  }
  if (expired.value) return { text: "Retirée", kind: "warn" };
  const missing = (o.keywords_asks ?? []).filter((a) => a.covered === false).map((a) => a.text);
  if (missing.length) return { text: `Il te manque : ${missing.slice(0, 3).join(", ")}`, kind: "gap" };
  if (o.remote_from_switzerland === false) return { text: "Télétravail fermé depuis la Suisse", kind: "warn" };
  return null;
});
const doubtText = computed(() => props.offer.doubts?.map((d) => d.text).join(" ") ?? "");
const location = computed(() =>
  [props.offer.location, props.showDate ? dateInList(props.offer.first_seen_at) : ""].filter(Boolean).join(" · ") || null,
);

// La limite de la formule (docs/125) explique une offre sans note.
const { reached } = usePlan();

function prepare(): void {
  void router.push(`/candidatures/offres/${props.offer.id}/preparer`);
}
</script>

<template>
  <OfferLine
    variant="full"
    :class="{ expired }"
    :title="offer.title"
    :company="offer.company ?? 'Entreprise non indiquée'"
    :location="location"
    :logo="offer.has_logo ? `/api/offers/${offer.id}/logo` : null"
    :note="alert?.text ?? null"
    :alert="!!alert && alert.kind !== 'gap'"
    :action="offer.status === 'preparing' ? 'Préparer' : null"
    :selected="selected"
    data-test="offer"
    @select="$emit('select')"
    @action="prepare"
  >
    <template #badges>
      <!-- Des étiquettes sans état : sans point, neutres (règle §4). -->
      <StatusPill
        v-if="offer.spontaneous"
        :dot="false"
        data-test="spontaneous-badge"
      >
        Spontanée
      </StatusPill>
      <StatusPill
        v-else-if="offer.added_by_you"
        :dot="false"
        data-test="added-badge"
      >
        Ajoutée par toi
      </StatusPill>
    </template>
    <template
      v-if="alert"
      #note
    >
      <span
        :title="alert.kind === 'danger' ? doubtText : undefined"
        data-test="offer-alert"
      >{{ alert.text }}<span
        v-if="alert.kind === 'danger' && doubtText"
        class="visually-hidden"
      > : {{ doubtText }}</span></span>
    </template>
    <template #verdict>
      <ScoreWord
        :score="offer.score ?? null"
        :pending="offer.summary_role ? 'Pas de note : aucun bloc de profil actif' : reached('score') ? 'Pas encore notée : les offres notées du mois sont utilisées' : 'Pas encore notée, à noter'"
        :stale="offer.score_stale"
      />
    </template>
  </OfferLine>
</template>
