<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Offer } from "../api/client";
import type { IconName } from "../icons";
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
// Une ligne de « À faire » : un nombre et un libellé ; ou, pour « Relire ton CV » (PR 22), une icône et une ligne de détail.
export type HomeTodo = { key: string; test: string; count: number; label: string; to: RouteLocationRaw; icon?: IconName; detail?: string };

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
  /** Un jour de repos (planche AccueilV2, état « repos », 14 novembre) : la phrase sous « Jour de repos. ». */
  restSub?: string | null;
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
      <!-- Un jour de repos : « Jour de repos. » à la main, puis la phrase (planche AccueilV2, état « repos »). -->
      <template v-if="restSub != null">
        <h1
          class="home-rest"
          data-test="home-rest"
        >
          <span>Jour de repos.</span>
        </h1>
        <p class="home-rest-sub">
          {{ restSub }}
        </p>
      </template>
      <h1 v-else>
        Bonjour{{ name ? ` ${name}` : "" }}.
      </h1>
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
        {{ restSub != null ? "Si tu veux avancer" : "À faire" }}
      </h2>
      <ul>
        <li
          v-for="todo in todos"
          :key="todo.key"
        >
          <RouterLink
            :to="todo.to"
            :class="{ 'home-todo-alert': todo.icon }"
            :data-test="todo.test"
          >
            <span
              v-if="todo.icon"
              class="home-todo-icon"
            ><AppIcon :name="todo.icon" /></span>
            <strong v-else>{{ todo.count }}</strong>
            <span v-if="todo.detail"><span class="home-todo-title">{{ todo.label }}</span><span class="home-todo-detail">{{ todo.detail }}</span></span>
            <span v-else>{{ todo.label }}</span>
            <AppIcon name="chevron" />
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<style>
/* Les styles de l'Accueil du téléphone, chargés avec lui (ils étaient dans style.css) : l'ordinateur ne les reçoit pas. */
/* --- L'Accueil du téléphone (docs/139 étape 4, maquette AccueilSmile) --- */
.home h1, .home h2 { margin: 0; font-weight: var(--weight-bold); letter-spacing: -0.03em; line-height: var(--leading-none); }
.home-hello { display: grid; gap: var(--space-4); padding: var(--space-5) var(--space-5) var(--space-12); }
.home-hello h1 { font-size: var(--title-hello); }
/* Un jour de repos (AccueilV2, état « repos ») : 25 px à la main, bleu, penché de 2° ; la phrase 15/22 dessous. */
.home-hello { --home-25: 1.5625rem; --home-15: 0.9375rem; --home-lh-22: 1.4667; }
.home-hello h1.home-rest { font-size: var(--home-25); font-weight: var(--weight-regular); letter-spacing: 0; }
.home-rest span { display: inline-block; font-family: var(--font-hand); color: var(--primary-text); transform: rotate(-2deg); }
.home-rest-sub { margin: 0; font-size: var(--home-15); line-height: var(--home-lh-22); color: var(--text-lead); }
.home-tagline { margin: 0; font-size: var(--font-section); font-weight: var(--weight-bold); color: var(--text-tertiary); }
.home-tagline s { text-decoration: line-through wavy var(--scribble) 3px; }
.home-tagline span { color: var(--primary-text); font-size: var(--font-page); }
.home-block { margin-top: calc(-1 * var(--radius-block)); padding: var(--space-6) var(--space-5) calc(var(--space-12) + var(--space-4)); border-radius: var(--radius-block) var(--radius-block) 0 0; }
.home-block h2 { font-size: var(--title-block); }
.home-orp { background: var(--primary-soft); }
.home-offers { background: var(--peach-soft); padding-inline: 0; }
.home-todo { background: var(--bg); padding-bottom: var(--space-6); }
/* Les bandes qui s'empilent au défilement (prompt du 10 novembre, fin de soirée, PR 36 ; maquettes AccueilSmile et
   AccueilSombre). ORP colle sous la barre du logo (--header-h), Offres 16 px plus bas avec une ombre vers le haut ; « À
   faire » ne colle pas et passe par-dessus. Une bande ne colle que si elle tient dans l'écran (.home-stick, posée par
   HomePhone.vue). Animations réduites : rien ne colle. Un lien ou un bouton qui prend le focus s'arrête sous la barre
   et le bord des bandes empilées (WCAG 2.4.11). */
@media (max-width: 820px) {
  .home { --home-stack-step: var(--space-4); --home-band-shadow: 0 -10px 24px rgb(27 31 42 / 10%); }
  .home-orp { position: relative; z-index: 1; }
  .home-offers { position: relative; z-index: 2; }
  .home-orp.home-stick { position: sticky; top: var(--header-h); }
  .home-offers.home-stick { position: sticky; top: calc(var(--header-h) + var(--home-stack-step)); }
  .home-offers, .home-todo { box-shadow: var(--home-band-shadow); }
  .home-todo { position: relative; z-index: 3; }
  .home :is(a, button, [tabindex]) {
    scroll-margin-top: calc(var(--header-h) + var(--home-stack-step) + var(--space-3));
    /* Ni sous la barre de navigation du bas (les dernières lignes de « À faire »). */
    scroll-margin-bottom: calc(var(--tabbar-h, 0px) + var(--space-3) + env(safe-area-inset-bottom));
  }
}
@media (max-width: 820px) and (prefers-reduced-motion: reduce) {
  .home-orp.home-stick, .home-offers.home-stick { position: relative; top: auto; }
}
.home-orp-link { display: flex; align-items: center; gap: var(--space-5); margin-top: var(--space-4); color: var(--text); font-size: var(--font-title); font-weight: var(--weight-bold); text-decoration: none; }
.home-orp-link > span { flex: 1; }
.home-block-head { display: flex; align-items: baseline; justify-content: space-between; padding: 0 var(--space-3) 0 var(--space-5); }
.home-block-head a { display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-2); font-weight: var(--weight-bold); text-decoration: none; }
.home-cards { display: flex; gap: var(--space-3); margin-top: var(--space-3); padding: 0 var(--space-5) var(--space-1); overflow-x: auto; scroll-snap-type: x mandatory; scroll-padding-left: var(--space-5); overscroll-behavior-x: contain; scrollbar-width: none; }
.home-card { flex: none; width: 17rem; display: grid; gap: var(--space-1); align-content: start; padding: var(--space-4); scroll-snap-align: start; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); color: var(--text); text-decoration: none; }
.home-card-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: var(--space-2); }
.home-card-where { font-size: var(--font-small); color: var(--text-secondary); }
.home-card-facts { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-2); }
.home-card-facts span { padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); background: var(--surface-muted); font-size: var(--font-caption); font-weight: var(--weight-semibold); color: var(--text-tertiary); }
.home-empty { display: flex; align-items: center; gap: var(--space-3); margin: var(--space-4) var(--space-5) 0; color: var(--text-secondary); }
.home-todo ul { margin: var(--space-4) 0 0; padding: 0; list-style: none; }
.home-todo li + li { border-top: 1px solid var(--line); }
.home-todo a { display: flex; align-items: center; gap: var(--space-4); min-height: 4rem; color: var(--text); font-weight: var(--weight-semibold); text-decoration: none; }
.home-todo strong { min-width: var(--space-8); font-size: var(--font-figure); color: var(--primary-text); }
.home-todo a > span { flex: 1; }
.home-todo .icon, .home-orp-link .icon { color: var(--text-secondary); }
/* « Relire ton CV » (AccueilSmile, variable cvNonLu ; PR 22) : l'icône document en pêche à la place du nombre, le titre
   de 16 gras et la ligne « Sans lui… » de 14 en pêche ; 72 de haut. */
.home-todo a.home-todo-alert { min-height: 4.5rem; gap: 0.875em; }
.home-todo a > .home-todo-icon { display: flex; flex: none; width: calc(var(--space-8) - 0.125rem); }
.home-todo .home-todo-icon .icon { color: var(--peach-text); width: var(--space-6); height: var(--space-6); }
.home-todo-title { display: block; font-size: var(--font-body); font-weight: var(--weight-bold); }
.home-todo-detail { display: block; font-size: var(--font-small); font-weight: var(--weight-semibold); color: var(--peach-text); }
.home-card { animation: content-in var(--t-standard) var(--ease-standard) backwards; }
</style>
