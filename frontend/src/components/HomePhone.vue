<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
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
// Les bandes qui s'empilent au défilement (prompt du 10 novembre, fin de soirée, PR 36 ; maquettes AccueilSmile et
// AccueilSombre, animation etats/AccueilSmile--bandes-empilees-animation.gif). ORP se colle sous la barre du logo
// (--header-h), Offres 16 px plus bas, « À faire » passe par-dessus. Le CSS fait l'empilement ; ici :
// - une bande ne colle que si elle tient dans la hauteur visible (sous la barre), mesuré au chargement et au
//   redimensionnement ;
// - toucher le bord visible d'une bande recouverte, ou y amener le focus, fait défiler jusqu'à elle (en douceur, ou
//   d'un coup si les animations sont réduites) ;
// - animations réduites : rien ne colle (aussi en CSS).
type Band = "orp" | "offers";
const bands = { orp: ref<HTMLElement | null>(null), offers: ref<HTMLElement | null>(null) };
const marks = { orp: ref<HTMLElement | null>(null), offers: ref<HTMLElement | null>(null) };
const todoBand = ref<HTMLElement | null>(null);
const sticks = reactive({ orp: false, offers: false });
const reduced = () => typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const headerHeight = () => document.querySelector(".topbar")?.getBoundingClientRect().height ?? 0;
// Où la bande s'arrête quand elle colle : son `top` calculé (--header-h, et 16 px de plus pour Offres).
const stickyTop = (band: Band) => parseFloat(getComputedStyle(bands[band].value!).top) || 0;

function measure(): void {
  const visible = window.innerHeight - headerHeight();
  for (const band of ["orp", "offers"] as const) {
    const el = bands[band].value;
    sticks[band] = Boolean(el) && !reduced() && el!.offsetHeight <= visible;
  }
}

// La bande est collée (sa place dans le flux est passée au-dessus) et la suivante la recouvre.
function covered(band: Band): boolean {
  const el = bands[band].value, mark = marks[band].value;
  const next = band === "orp" ? bands.offers.value : todoBand.value;
  if (!sticks[band] || !el || !mark || !next) return false;
  const top = el.getBoundingClientRect().top;
  return mark.getBoundingClientRect().top < top - 1 && next.getBoundingClientRect().top < el.getBoundingClientRect().bottom - 1;
}

function scrollToBand(band: Band, smooth: boolean): void {
  const el = bands[band].value, mark = marks[band].value;
  if (!el || !mark) return;
  // La place de la bande dans le flux : la marque juste avant elle, moins le chevauchement (marge haute négative).
  const top = mark.getBoundingClientRect().top + window.scrollY + parseFloat(getComputedStyle(el).marginTop) - stickyTop(band);
  window.scrollTo({ top, behavior: smooth && !reduced() ? "smooth" : "auto" });
}

function onBandClick(band: Band, event: MouseEvent): void {
  if (!covered(band)) return;
  event.preventDefault();
  event.stopPropagation();
  scrollToBand(band, true);
}
// Clavier (WCAG 2.4.11) : un élément qui prend le focus dans une bande recouverte n'y reste pas caché.
function onBandFocus(band: Band): void {
  if (covered(band)) scrollToBand(band, false);
}

let observer: ResizeObserver | null = null;
onMounted(() => {
  measure();
  window.addEventListener("resize", measure);
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(measure);
    for (const el of [bands.orp.value, bands.offers.value]) if (el) observer.observe(el);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", measure);
  observer?.disconnect();
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

    <div
      :ref="(el) => (marks.orp.value = el as HTMLElement | null)"
      class="home-mark"
      aria-hidden="true"
    />
    <section
      :ref="(el) => (bands.orp.value = el as HTMLElement | null)"
      :class="['home-block', 'home-orp', { 'home-stick': sticks.orp }]"
      aria-labelledby="home-orp-title"
      data-test="home-band-orp"
      @click.capture="onBandClick('orp', $event)"
      @focusin="onBandFocus('orp')"
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

    <div
      :ref="(el) => (marks.offers.value = el as HTMLElement | null)"
      class="home-mark"
      aria-hidden="true"
    />
    <section
      :ref="(el) => (bands.offers.value = el as HTMLElement | null)"
      :class="['home-block', 'home-offers', { 'home-stick': sticks.offers }]"
      aria-labelledby="home-offers-title"
      data-test="home-band-offers"
      @click.capture="onBandClick('offers', $event)"
      @focusin="onBandFocus('offers')"
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
      ref="todoBand"
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
