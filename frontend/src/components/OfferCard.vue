<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import type { Offer } from "../api/client";
import { dateInList } from "../dates";
import { cityOnly, rateText, remoteText } from "../format";
import AppIcon from "./AppIcon.vue";
import OfferLine from "./OfferLine.vue";
import ScoreRing from "./ScoreRing.vue";
import StatusPill from "./StatusPill.vue";
import { usePlan } from "../composables/usePlan";
import { usePhone } from "../composables/usePhone";

// Une offre dans la liste d'Offres : la Ligne d'offre complète (planche « Ligne d'offre », 1.6.7x) ;
// le détail s'ouvre à droite. Toute la ligne sélectionne l'offre ; pas de mot d'action sur une offre
// nouvelle (choix de Kevin), « Préparer » seulement sur une offre gardée. La date n'y est que hors du
// tri « Par jour », où la ligne du jour la donne.
const props = defineProps<{ offer: Offer; selected: boolean; showDate?: boolean }>();
defineEmits<{ select: []; more: [] }>();
// Téléphone (C6, Kevin 2026-11-05) : le « ⋯ » de 44 px dans le coin en haut à droite ouvre ses actions ;
// « Préparer » n'est plus sur la carte : la fiche l'a (« Reprendre la lettre »).
const { phone } = usePhone();
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
  // Sur téléphone, la carte reste celle de la maquette : ce qui manque est dans la fiche (Kevin, 2026-11-05).
  if (missing.length && !phone.value) return { text: `Il te manque : ${missing.slice(0, 3).join(", ")}`, kind: "gap" };
  if (o.remote_from_switzerland === false) return { text: "Télétravail fermé depuis la Suisse", kind: "warn" };
  return null;
});
// Les faits de l'offre en pastilles, comme sur l'Accueil (docs/139, étape 5b).
const facts = computed(() =>
  [rateText(props.offer.rate_min, props.offer.rate_max), props.offer.employment_type ?? "", remoteText(props.offer, phone.value) ?? ""].filter(Boolean),
);
// À traiter mêle trois statuts (C2) : la carte dit quand elle est en préparation ou gardée pour plus tard.
// Sur téléphone, « En préparation » est le titre de la section, pas une étiquette (Kevin, 2026-11-05).
const statusTag = computed(() =>
  props.offer.status === "preparing" && !phone.value ? "En préparation" : props.offer.status === "later" ? "Plus tard" : null,
);
const doubtText = computed(() => props.offer.doubts?.map((d) => d.text).join(" ") ?? "");
const location = computed(() =>
  [phone.value ? cityOnly(props.offer.location) : props.offer.location, props.showDate ? dateInList(props.offer.first_seen_at) : ""].filter(Boolean).join(" · ") || null,
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
    :action="offer.status === 'preparing' && !phone ? 'Préparer' : null"
    :selected="selected"
    data-test="offer"
    @select="$emit('select')"
    @action="prepare"
  >
    <template #badges>
      <StatusPill
        v-if="statusTag"
        :dot="false"
        :class="['offer-status-tag', offer.status]"
        data-test="status-tag"
      >
        {{ statusTag }}
      </StatusPill>
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
    <template
      v-if="facts.length"
      #facts
    >
      <span
        class="offer-facts"
        data-test="offer-facts"
      >
        <span
          v-for="fact in facts"
          :key="fact"
        >{{ fact }}</span>
      </span>
    </template>
    <!-- D3 (C7) : l'anneau sans chiffre, le mot dessous ; le chiffre pour les lecteurs d'écran. -->
    <template
      v-if="phone"
      #corner
    >
      <button
        type="button"
        class="offer-more"
        :aria-label="`Actions pour ${offer.title}`"
        data-test="offer-more"
        @click="$emit('more')"
      >
        <AppIcon name="more" />
      </button>
    </template>
    <template #verdict>
      <ScoreRing
        worded
        :score="offer.score ?? null"
        :pending="offer.summary_role ? 'Pas de note : aucun bloc de profil actif' : reached('score') ? 'Pas encore notée : les offres notées du mois sont utilisées' : 'Pas encore notée, à noter'"
        :stale="offer.score_stale"
      />
    </template>
  </OfferLine>
</template>
