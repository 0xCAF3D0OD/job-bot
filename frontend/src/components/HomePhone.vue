<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Offer } from "../api/client";
import { plural, rateText, remoteText } from "../format";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import FaceMark from "./FaceMark.vue";
import LiquidCircle from "./LiquidCircle.vue";
import ScoreRing from "./ScoreRing.vue";

// L'Accueil du téléphone (docs/139 étape 4, maquette AccueilSmile ; écarts A1 à A9 validés le 2026-11-02) :
// « Bonjour Kevin. », puis trois blocs qui se chevauchent : ORP (le cercle liquide), Offres (les cartes de la
// dose du jour et « Trier les n offres », seul bouton plein de l'accueil, A3), À faire (un nombre, un
// libellé). L'ordinateur garde sa page.
export type HomeTodo = { key: string; test: string; count: number; label: string; to: RouteLocationRaw };

const props = defineProps<{
  name: string | null;
  firstDay: boolean;
  month: string;
  count: number;
  target: number | null;
  offers: Offer[];
  canTriage: boolean;
  emptyText: string;
  todos: HomeTodo[];
}>();

// « d'ici le 30 nov. » : le dernier jour du mois ORP.
const monthEnd = computed(() => {
  const [year, month] = props.month.split("-").map(Number);
  const last = new Date(year!, month!, 0);
  return new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" }).format(last);
});
const orpLine = computed(() => {
  if (!props.target) return `${plural(props.count, "recherche", "recherches")} ce mois.`;
  const left = props.target - props.count;
  return left > 0 ? `Encore ${left} d'ici le ${monthEnd.value}` : "Objectif du mois atteint.";
});
function facts(offer: Offer): string[] {
  return [rateText(offer.rate_min, offer.rate_max), offer.employment_type ?? "", remoteText(offer) ?? ""].filter(Boolean);
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
      <template v-if="canTriage">
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
            <span class="home-card-where">{{ [offer.company, offer.location].filter(Boolean).join(" · ") }}</span>
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
        <RouterLink
          :to="{ name: 'triage' }"
          class="button-link primary-link home-triage"
          data-test="home-triage"
        >
          Trier les {{ offers.length === 1 ? "1 offre" : `${offers.length} offres` }}
        </RouterLink>
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
