<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";

// « Pour cette offre » (MODIFICATIONS du 8 novembre au soir, lot 15.1 ; capture PreparerOrdinateur) : « n points
// forts · n à vérifier », puis deux groupes. Chaque élément : le sujet en gras (la partie avant les deux-points des
// données), le détail dessous. Plus de verdict ni de repli : tout est montré. La coche et le point d'attention
// disent le groupe avec la couleur (WCAG 1.4.1).
const props = defineProps<{ offer: Offer }>();

type Point = { subject: string; detail: string };
function split(text: string): Point {
  const at = text.indexOf(":");
  if (at <= 0) return { subject: text.trim(), detail: "" };
  const detail = text.slice(at + 1).trim();
  return { subject: text.slice(0, at).trim(), detail: detail ? detail.charAt(0).toUpperCase() + detail.slice(1) : "" };
}
const strengths = computed(() => (props.offer.strengths ?? []).map((p) => split(p.text)));
const gaps = computed(() => (props.offer.gaps ?? []).map((p) => split(p.text)));
const head = computed(() =>
  [
    strengths.value.length ? plural(strengths.value.length, "point fort", "points forts") : "",
    gaps.value.length ? `${gaps.value.length} à vérifier` : "",
  ]
    .filter(Boolean)
    .join(" · "),
);
const groups = computed(() =>
  [
    { key: "ok", title: `Points forts (${strengths.value.length})`, icon: "check" as const, items: strengths.value },
    { key: "gap", title: `À vérifier (${gaps.value.length})`, icon: "alert-circle" as const, items: gaps.value },
  ].filter((g) => g.items.length),
);
</script>

<template>
  <section
    v-if="offer.summary_role"
    class="side-card offer-brief"
    aria-labelledby="offer-brief-title"
    data-test="offer-brief"
  >
    <h2 id="offer-brief-title">
      Pour cette offre
    </h2>
    <p
      v-if="head"
      class="offer-brief-head"
      data-test="offer-brief-head"
    >
      {{ head }}
    </p>
    <div
      v-for="group in groups"
      :key="group.key"
      :class="['offer-brief-group', group.key]"
      :data-test="`offer-brief-${group.key}`"
    >
      <h3>{{ group.title }}</h3>
      <ul>
        <li
          v-for="point in group.items"
          :key="point.subject + point.detail"
        >
          <AppIcon :name="group.icon" />
          <span>
            <strong>{{ point.subject }}</strong>
            <span
              v-if="point.detail"
              class="offer-brief-detail"
            >{{ point.detail }}</span>
          </span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style>
/* Valeurs du lot 15.1 : sous-titre 14 --text-secondary ; groupes en 14/700 ; éléments en 10 px de marge, sujet 15/700,
   détail 14 --text-tertiary ; coche --success, point d’attention --peach-text. */
.offer-brief { --brief-10: 10px; --brief-icon: 18px; }
.offer-brief .offer-brief-head { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.offer-brief-group h3 { margin: var(--space-4) 0 0; font-size: var(--font-small); font-weight: var(--weight-bold); }
.offer-brief-group ul { margin: 0; padding: 0; list-style: none; }
.offer-brief-group li { display: flex; align-items: flex-start; gap: var(--space-3); padding: var(--brief-10) 0; }
.offer-brief-group li > .icon { flex: none; width: var(--brief-icon); height: var(--brief-icon); }
.offer-brief-group.ok li > .icon { color: var(--success); }
.offer-brief-group.gap li > .icon { color: var(--peach-text); }
.offer-brief-group li > span { display: grid; min-width: 0; }
.offer-brief-group strong { font-size: var(--font-label); font-weight: var(--weight-bold); line-height: var(--leading-tight); }
.offer-brief-detail { font-size: var(--font-small); color: var(--text-tertiary); line-height: var(--leading-normal); }
</style>
