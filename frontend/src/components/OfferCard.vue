<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { dayShort } from "../format";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import ScoreRing from "./ScoreRing.vue";

// Une offre sur une ligne (docs/73 §4) : de quoi choisir ; le détail est dans le panneau de
// droite. La date n'y est que hors du tri « Par jour », où la ligne du jour la donne.
const props = defineProps<{ offer: Offer; selected: boolean; showDate?: boolean }>();
defineEmits<{ select: [] }>();

const expired = computed(() => Boolean(props.offer.expired_at) && props.offer.status !== "applied");
// Une seule alerte, la plus utile pour décider : écartée, douteuse, retirée, puis ce qui manque.
const alert = computed<{ text: string; kind: "warn" | "danger" } | null>(() => {
  const o = props.offer;
  if (o.filter_reasons?.length) return { text: o.filter_reasons[0]!, kind: "warn" };
  if (o.doubts?.length) {
    const scam = o.doubts.some((d) => d.kind === "scam");
    return { text: scam ? "Arnaque possible" : "À vérifier", kind: "danger" };
  }
  if (expired.value) return { text: "Retirée", kind: "warn" };
  const missing = (o.keywords_asks ?? []).filter((a) => a.covered === false).map((a) => a.text);
  if (missing.length) return { text: `Il te manque : ${missing.slice(0, 3).join(", ")}`, kind: "warn" };
  if (o.remote_from_switzerland === false) return { text: "Télétravail fermé depuis la Suisse", kind: "warn" };
  return null;
});
const doubtText = computed(() => props.offer.doubts?.map((d) => d.text).join(" ") ?? "");
</script>

<template>
  <button
    type="button"
    :class="['offer-row', { selected, expired }]"
    :aria-pressed="selected"
    data-test="offer"
    @click="$emit('select')"
  >
    <CompanyLogo :offer="offer" />
    <span class="offer-row-main">
      <span class="offer-row-title">
        {{ offer.title }}
        <span
          v-if="offer.spontaneous"
          class="badge spontaneous-badge"
          data-test="spontaneous-badge"
        >Spontanée</span>
        <span
          v-else-if="offer.added_by_you"
          class="badge spontaneous-badge"
          data-test="added-badge"
        >Ajoutée par toi</span>
      </span>
      <span class="offer-row-sub meta-line">
        <span><AppIcon name="building" /><span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée" }}</span>
        <span v-if="offer.location"><AppIcon name="pin" /><span class="visually-hidden">Lieu : </span>{{ offer.location }}</span>
        <span
          v-if="showDate"
          data-test="offer-date"
        ><AppIcon name="clock" /><span class="visually-hidden">Repérée le </span>{{ dayShort(offer.first_seen_at) }}</span>
      </span>
      <span
        v-if="alert"
        :class="['offer-row-alert', alert.kind]"
        :title="alert.kind === 'danger' ? doubtText : undefined"
        data-test="offer-alert"
      >{{ alert.text }}<span
        v-if="alert.kind === 'danger' && doubtText"
        class="visually-hidden"
      > : {{ doubtText }}</span></span>
    </span>
    <ScoreRing
      :score="offer.score ?? null"
      :pending="offer.summary_role ? 'Pas de note : aucun bloc de profil actif' : 'Pas encore notée, à noter'"
      :stale="offer.score_stale"
    />
  </button>
</template>
