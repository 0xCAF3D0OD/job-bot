<script setup lang="ts">
// « Autres offres chez … » de la fiche d’une offre (planche Offre du 18.11), téléphone seulement.
// Chargé à part (defineAsyncComponent dans OfferDetail) pour garder la page Candidatures sous sa limite de poids.
import { ref, watch } from "vue";
import { api, type Offer } from "../api/client";
import { dateInList } from "../dates";
import { cityOnly, rateText, scoreWord } from "../format";
import { displayTitle } from "../offerTitle";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer }>();

// « Autres offres chez … » (planche Offre) : les offres de la même entreprise, lues avec la recherche de la liste ;
// trois au plus, le nombre total dans le titre. Rien si l'entreprise n'est pas connue ou n'a pas d'autre offre.
type Sibling = Pick<Offer, "id" | "title" | "company" | "location" | "rate_min" | "rate_max" | "score" | "status" | "first_seen_at">;
const SIBLINGS_MAX = 3;
const siblings = ref<Sibling[]>([]);
const companyKey = (name: string | null | undefined) => (name ?? "").trim().toLocaleLowerCase("fr");
async function loadSiblings() {
  const offer = props.offer;
  const key = companyKey(offer.company);
  siblings.value = [];
  if (!key) return;
  const { data } = await api.GET("/api/offers", { params: { query: { q: offer.company!.trim(), view: "all", sort: "recent", limit: 50 } } });
  if (props.offer.id !== offer.id) return;
  siblings.value = (data?.items ?? []).filter((o) => o.id !== offer.id && companyKey(o.company) === key);
}
watch(() => [props.offer.id, props.offer.company], () => void loadSiblings().catch(() => (siblings.value = [])), { immediate: true });
// « Lausanne · 100 % · 16 nov. » : la date suit la règle des dates de l'app (la planche écrit « il y a 5 j »).
function siblingLine(o: Sibling): string {
  return [cityOnly(o.location), rateText(o.rate_min, o.rate_max), o.first_seen_at ? dateInList(o.first_seen_at) : ""].filter(Boolean).join(" · ");
}
</script>

<template>
  <!-- « Autres offres chez … » (planche Offre du 18.11) : trois au plus, la note ou « Envoyée », vers leur fiche. -->
  <section
    v-if="siblings.length"
    class="company-offers"
    aria-labelledby="company-offers-title"
    data-test="company-offers"
  >
    <h3 id="company-offers-title">
      Autres offres chez {{ offer.company }} · {{ siblings.length }}
    </h3>
    <RouterLink
      v-for="other in siblings.slice(0, SIBLINGS_MAX)"
      :key="other.id"
      :to="`/candidatures/offres/${other.id}`"
      class="company-offer"
      data-test="company-offer"
    >
      <span class="company-offer-text">
        <b>{{ displayTitle(other.title, other) }}</b>
        <span>{{ siblingLine(other) }}</span>
      </span>
      <span
        v-if="other.status === 'applied'"
        class="company-offer-pill"
      >Envoyée</span>
      <span
        v-else-if="other.score != null"
        :class="['company-offer-pill', scoreWord(other.score).tone]"
      ><span class="visually-hidden">Note </span>{{ other.score }}</span>
      <AppIcon name="chevron" />
    </RouterLink>
  </section>
</template>

<style>
.company-offers { --co-title: 17px; --co-title-lh: 22px; --co-line: 13px; --co-line-lh: 18px; --co-pill-y: 4px; --co-pill-x: 8px; --co-chevron: 20px; --co-gap: 4px; }
.company-offers h3 { margin: 0 0 var(--space-1); font-size: var(--co-title); line-height: var(--co-title-lh); font-weight: var(--weight-bold); }
.company-offer { display: flex; align-items: center; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-3) 0; color: inherit; text-decoration: none; }
.company-offer + .company-offer { border-top: 1px solid var(--line); }
.company-offer-text { flex: 1; min-width: 0; }
.company-offer-text b { display: block; overflow: hidden; font-size: var(--font-label); line-height: var(--co-title-lh); white-space: nowrap; text-overflow: ellipsis; }
.company-offer-text > span { display: block; margin-top: var(--co-gap); font-size: var(--co-line); line-height: var(--co-line-lh); color: var(--text-secondary); }
.company-offer-pill { flex: none; padding: var(--co-pill-y) var(--co-pill-x); border-radius: var(--radius-pill); background: var(--surface-muted); color: var(--text-tertiary); font-size: var(--co-line); font-weight: var(--weight-bold); }
.company-offer-pill:is(.very-close, .close) { background: var(--success-soft); color: var(--success); }
.company-offer > .icon { flex: none; width: var(--co-chevron); height: var(--co-chevron); color: var(--primary-text); }
</style>
