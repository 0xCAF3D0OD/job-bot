<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Offer } from "../api/client";
import { companyPlace, orpLeftLine, plural, rateText, remoteText } from "../format";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import FaceMark from "./FaceMark.vue";
import LiquidCircle from "./LiquidCircle.vue";
import ScoreRing from "./ScoreRing.vue";

// L'Accueil du téléphone (docs/139 étape 4, maquette AccueilSmile ; écarts A1 à A9 validés le 2026-11-02) :
// « Bonjour Kevin. », puis trois blocs qui se chevauchent : ORP (le cercle liquide), Offres (les cartes de la
// dose du jour, tant qu'il y en a, et « Tout voir » ; sans bouton « Trier », A3 annulé le 2026-11-05 par
// Kevin), À faire (un nombre, un libellé). L'ordinateur garde sa page.
export type HomeTodo = { key: string; test: string; count: number; label: string; to: RouteLocationRaw };

const props = defineProps<{
  name: string | null;
  firstDay: boolean;
  month: string;
  count: number;
  target: number | null;
  /** L'échéance ORP du mois (le 5 du mois suivant, reporté au jour ouvrable du canton). */
  due?: string | null;
  offers: Offer[];
  emptyText: string;
  todos: HomeTodo[];
}>();

// « Encore 2 d’ici le 5 décembre » : l'échéance ORP du mois, pas sa fin (MODIFICATIONS du 9 novembre, §11).
const orpLine = computed(() => {
  if (!props.target) return `${plural(props.count, "recherche", "recherches")} ce mois.`;
  return orpLeftLine(props.count, props.target, props.month, props.due);
});
function facts(offer: Offer): string[] {
  return [rateText(offer.rate_min, offer.rate_max), offer.employment_type ?? "", remoteText(offer, true) ?? ""].filter(Boolean);
}
</script>

<template>
  <div
    class="home"
    data-test="home-phone"
  >
    <div class="home-hello">
      <h1>Bonjour{{ name ? ` ${name}` : "" }}.</h1>
      <!-- L'accroche, à la première ouverture seulement (A8). -->
      <p
        v-if="firstDay"
        class="home-tagline"
        data-test="home-tagline"
      >
        Moins <s>chercher</s>,<br><span>plus vivre.</span>
      </p>
      <slot />
    </div>

    <section
      class="home-block home-orp"
      aria-labelledby="home-orp-title"
    >
      <h2 id="home-orp-title">
        ORP
      </h2>
      <RouterLink
        to="/bilan"
        class="home-orp-link"
        data-test="home-orp"
      >
        <LiquidCircle
          v-if="target"
          :count="count"
          :target="target"
        />
        <span>{{ orpLine }}</span>
        <AppIcon name="chevron" />
      </RouterLink>
    </section>

    <section
      class="home-block home-offers"
      aria-labelledby="home-offers-title"
    >
      <div class="home-block-head">
        <h2 id="home-offers-title">
          Offres
        </h2>
        <RouterLink
          :to="{ path: '/candidatures/offres' }"
          data-test="home-offers-all"
        >
          Tout voir
        </RouterLink>
      </div>
      <template v-if="offers.length">
        <div
          class="home-cards"
          role="region"
          aria-label="Offres du jour, défilement horizontal"
          tabindex="0"
        >
          <RouterLink
            v-for="offer in offers"
            :key="offer.id"
            :to="{ path: '/candidatures/offres', query: { offre: String(offer.id) } }"
            class="home-card"
            data-test="home-card"
          >
            <span class="home-card-top">
              <CompanyLogo :offer="offer" />
              <ScoreRing
                :score="offer.score ?? null"
                worded
              />
            </span>
            <strong>{{ offer.title }}</strong>
            <span class="home-card-where">{{ companyPlace(offer.company, offer.location, true) }}</span>
            <span
              v-if="facts(offer).length"
              class="home-card-facts"
            >
              <span
                v-for="fact in facts(offer)"
                :key="fact"
              >{{ fact }}</span>
            </span>
          </RouterLink>
        </div>
      </template>
      <p
        v-else
        class="home-empty"
        data-test="home-offers-empty"
      >
        <FaceMark
          mood="content"
          :size="32"
        />
        {{ emptyText }}
      </p>
    </section>

    <section
      v-if="todos.length"
      class="home-block home-todo"
      aria-labelledby="home-todo-title"
      data-test="home-todo"
    >
      <h2 id="home-todo-title">
        À faire
      </h2>
      <ul>
        <li
          v-for="todo in todos"
          :key="todo.key"
        >
          <RouterLink
            :to="todo.to"
            :data-test="todo.test"
          >
            <strong>{{ todo.count }}</strong>
            <span>{{ todo.label }}</span>
            <AppIcon name="chevron" />
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>
