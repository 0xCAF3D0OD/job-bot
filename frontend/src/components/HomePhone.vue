<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Offer } from "../api/client";
import { companyPlace, plural, scoreWord } from "../format";
import AppIcon from "./AppIcon.vue";
import BookmarkMark from "./BookmarkMark.vue";
import CompanyLogo from "./CompanyLogo.vue";
import OrpBar from "./OrpBar.vue";
import TriageNone from "./TriageNone.vue";
import "../triage.css";

// L'Accueil du téléphone (lot du 11 novembre au soir, PR 49 ; maquettes AccueilV2 et AccueilV2Sombre, états
// « accueil » et « vide »). L'accroche : « Bonjour Kevin. », ou, avec un justificatif en retard, deux lignes
// manuscrites (le retard en brun, la suite en bleu) et le personnage à la liste. Puis trois bandes qui se
// chevauchent : « À faire » (tâches numérotées, celle en retard en numéro 1, en brun), ORP (la barre ORP, PR 48) et
// « {n} offres à trier » (la meilleure offre en petite carte, la pile derrière, « Trier les offres ») ou, sans offre,
// « Rien à trier pour l’instant ». L'ordinateur a sa page (TodayView).
export type HomeTodo = { key: string; test: string; title: string; detail: string; to: RouteLocationRaw; late?: boolean };
// L'accroche d'un justificatif en retard : « 1 justificatif en retard, » puis « puis 2 candidatures ».
export type HomeLate = { hand: string; then: string | null; sub: string };

const props = defineProps<{
  name: string | null;
  firstDay: boolean;
  month: string;
  count: number;
  target: number | null;
  /** L'échéance ORP du mois (le 5 du mois suivant, reporté au jour ouvrable du canton). */
  due?: string | null;
  /** La semaine en cours (lot du 11 novembre au soir, PR 48) : « Cette semaine · 2 sur 3 » sous la barre. */
  week?: { count: number; target: number } | null;
  late?: HomeLate | null;
  /** Les offres à trier aujourd'hui, la meilleure d'abord ; vide : « Rien à trier pour l’instant ». */
  offers: Offer[];
  /** Jour de repos, pause, tri fini : la raison, à la place de « Rien à trier pour l’instant ». */
  emptyTitle?: string;
  /** « Élargir ma recherche » : seulement quand il n'y a vraiment aucune offre. */
  widen?: boolean;
  todos: HomeTodo[];
}>();

// Sans objectif saisi : le nombre du mois, sans barre. Avec : la barre ORP (OrpBar, PR 48).
const orpLine = computed(() => `${plural(props.count, "recherche", "recherches")} ce mois.`);
// Les bandes qui s'empilent au défilement (prompt du 10 novembre, fin de soirée, PR 36), dans l'ordre de la maquette du
// 11 novembre : « À faire » se colle sous la barre du logo (--header-h), ORP 16 px plus bas, les offres à trier passent
// par-dessus. Le CSS fait l'empilement ; ici :
// - une bande ne colle que si elle tient dans la hauteur visible (sous la barre), mesuré au chargement et au
//   redimensionnement ;
// - toucher le bord visible d'une bande recouverte, ou y amener le focus, fait défiler jusqu'à elle (en douceur, ou
//   d'un coup si les animations sont réduites) ;
// - animations réduites : rien ne colle (aussi en CSS).
type Band = "todo" | "orp";
const bands = { todo: ref<HTMLElement | null>(null), orp: ref<HTMLElement | null>(null) };
const marks = { todo: ref<HTMLElement | null>(null), orp: ref<HTMLElement | null>(null) };
const offersBand = ref<HTMLElement | null>(null);
const sticks = reactive({ todo: false, orp: false });
const reduced = () => typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const headerHeight = () => document.querySelector(".topbar")?.getBoundingClientRect().height ?? 0;
// Où la bande s'arrête quand elle colle : son `top` calculé (--header-h, et 16 px de plus pour ORP).
const stickyTop = (band: Band) => parseFloat(getComputedStyle(bands[band].value!).top) || 0;

function measure(): void {
  const visible = window.innerHeight - headerHeight();
  for (const band of ["todo", "orp"] as const) {
    const el = bands[band].value;
    sticks[band] = Boolean(el) && !reduced() && el!.offsetHeight <= visible;
  }
}

// La bande est collée (sa place dans le flux est passée au-dessus) et la suivante la recouvre.
function covered(band: Band): boolean {
  const el = bands[band].value, mark = marks[band].value;
  const next = band === "todo" ? bands.orp.value : offersBand.value;
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
    for (const el of [bands.todo.value, bands.orp.value]) if (el) observer.observe(el);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", measure);
  observer?.disconnect();
});

// La meilleure offre, en petite carte : son libellé de note en minuscules (« proche »), dans la couleur de la note.
const best = computed(() => props.offers[0] ?? null);
const bestWord = computed(() => (best.value?.score == null ? null : scoreWord(best.value.score)));
// « Remettre » en gras, la suite en demi-gras (maquette).
function verb(title: string): [string, string] {
  const at = title.indexOf(" ");
  return at < 0 ? [title, ""] : [title.slice(0, at), title.slice(at)];
}
</script>

<template>
  <div
    class="home"
    data-test="home-phone"
  >
    <div :class="['home-hello', { 'home-hello-late': late }]">
      <div
        v-if="late"
        class="home-late"
      >
        <div>
          <h1 data-test="home-late">
            <span class="home-hand home-hand-late">{{ late.hand }}</span><template v-if="late.then">
              <br><span class="home-hand">{{ late.then }}</span>
            </template>
          </h1>
          <p>{{ late.sub }}</p>
        </div>
        <img
          src="/tri/orange-liste.webp"
          alt=""
          width="116"
          height="112"
        >
      </div>
      <template v-else>
        <h1>Bonjour{{ name ? ` ${name}` : "" }}.</h1>
        <!-- L'accroche, à la première ouverture seulement (A8). -->
        <p
          v-if="firstDay"
          class="home-tagline"
          data-test="home-tagline"
        >
          Moins <s>chercher</s>,<br><span>plus vivre.</span>
        </p>
      </template>
      <slot />
    </div>

    <template v-if="todos.length">
      <div
        :ref="(el) => (marks.todo.value = el as HTMLElement | null)"
        class="home-mark"
        aria-hidden="true"
      />
      <section
        :ref="(el) => (bands.todo.value = el as HTMLElement | null)"
        :class="['home-block', 'home-todo', { 'home-stick': sticks.todo }]"
        aria-labelledby="home-todo-title"
        data-test="home-todo"
        @click.capture="onBandClick('todo', $event)"
        @focusin="onBandFocus('todo')"
      >
        <div class="home-block-head">
          <h2 id="home-todo-title">
            À faire
          </h2>
        </div>
        <ol>
          <li
            v-for="(todo, i) in todos"
            :key="todo.key"
          >
            <RouterLink
              :to="todo.to"
              :class="{ 'home-todo-late': todo.late }"
              :data-test="`todo-${todo.test}`"
            >
              <b
                class="home-todo-num"
                aria-hidden="true"
              >{{ i + 1 }}</b>
              <span class="home-todo-text">
                <b>{{ verb(todo.title)[0] }}<span>{{ verb(todo.title)[1] }}</span></b>
                <span>{{ todo.detail }}</span>
              </span>
              <AppIcon name="chevron" />
            </RouterLink>
          </li>
        </ol>
      </section>
    </template>

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
      <div class="home-block-head">
        <h2 id="home-orp-title">
          ORP
        </h2>
        <RouterLink
          to="/bilan"
          data-test="home-orp"
        >
          Voir le suivi
        </RouterLink>
      </div>
      <OrpBar
        v-if="target"
        class="home-orp-bar"
        :month="month"
        :count="count"
        :target="target"
        :due="due"
        :week="week"
        pace
      />
      <p
        v-else
        class="home-orp-none"
      >
        {{ orpLine }}
      </p>
    </section>

    <section
      ref="offersBand"
      class="home-block home-offers"
      aria-labelledby="home-offers-title"
      data-test="home-band-offers"
    >
      <div class="home-block-head">
        <h2 id="home-offers-title">
          {{ best ? plural(offers.length, "offre à trier", "offres à trier") : "Offres à trier" }}
        </h2>
        <span v-if="best">La meilleure d’abord</span>
      </div>
      <template v-if="best">
        <div class="tri-peek">
          <span
            v-if="offers.length > 2"
            class="tri-peek-pile tri-peek-far"
            aria-hidden="true"
          />
          <span
            v-if="offers.length > 1"
            class="tri-peek-pile tri-peek-near"
            aria-hidden="true"
          />
          <div
            class="tri-peek-card"
            data-test="home-card"
          >
            <CompanyLogo :offer="best" />
            <div>
              <b>{{ best.title }}</b>
              <span class="tri-peek-sub"><span>{{ companyPlace(best.company || "Entreprise non indiquée", best.location, true) }}</span><template v-if="bestWord">
                <span aria-hidden="true">·</span><b :class="`tone-${bestWord.tone}`">{{ bestWord.word.toLowerCase() }}</b>
              </template></span>
            </div>
            <BookmarkMark
              class="tri-peek-bookmark"
              :width="30"
            />
          </div>
        </div>
        <RouterLink
          :to="{ name: 'triage' }"
          class="home-triage"
          data-test="home-triage"
        >
          Trier les offres<AppIcon name="arrow-right" />
        </RouterLink>
      </template>
      <TriageNone
        v-else
        class="home-none"
        :title="emptyTitle"
        :widen="widen"
      />
    </section>
  </div>
</template>

<style scoped>
/* Les valeurs des maquettes AccueilV2 et AccueilV2Sombre, écrites avec les échelles ; les tailles hors échelle sont
   nommées ici. Hors grille de 4, ramenés à la grille : marge 22 px au-dessus de la petite carte (24), sa marge
   intérieure de 14 px (16), 14 px au-dessus du bouton (16), 6 px au-dessus du bloc vide (8). */
.home {
  --h-r: 32px; --h-over: -28px; --h-26: 1.625rem; --h-25: 1.5625rem; --h-15: 0.9375rem; --h-22: 1.375rem; --h-16: 1rem; --h-14: 0.875rem; --h-20: 1.25rem; --h-44: 44px;
  --h-num: 32px; --h-row: 72px; --h-img: 112px; --h-peek-r: 18px; --h-pile: 30px; --h-pile-r: 16px; --h-logo: 40px; --h-60: 60px; --h-btn: 48px; --h-18: 18px; --h-3: 3px;
  --h-far: 20px; --h-far-up: -12px; --h-near: 9px; --h-near-up: -6px; --h-mark-up: -14px;
  --home-stack-step: var(--space-4); --home-band-shadow: 0 -6px 16px rgb(27 31 42 / 6%);
}
.home h1, .home h2 { margin: 0; }
.home-hello { display: grid; gap: var(--space-4); padding: var(--space-5) var(--space-5) var(--space-12); }
.home-hello > h1 { font-size: var(--title-hello); font-weight: var(--weight-bold); letter-spacing: -0.03em; line-height: var(--leading-none); }
.home-hello-late { padding: var(--space-2) var(--space-6) var(--h-44); }
.home-late { display: flex; align-items: center; gap: var(--space-2); }
.home-late > div { flex: 1; min-width: 0; }
.home-late h1 { font-size: var(--h-25); line-height: var(--leading-none); font-weight: var(--weight-regular); }
.home-hand { display: inline-block; font-family: var(--font-hand); font-size: var(--h-25); line-height: var(--leading-none); color: var(--primary-text); transform: rotate(-2deg); }
.home-hand-late { color: var(--peach-text); }
.home-late p { margin: var(--space-3) 0 0; font-size: var(--h-15); line-height: var(--h-22); color: var(--text-lead); }
.home-late img { flex: none; width: auto; height: var(--h-img); }
.home-tagline { margin: 0; font-size: var(--font-section); font-weight: var(--weight-bold); color: var(--text-tertiary); }
.home-tagline s { text-decoration: line-through wavy var(--scribble) 3px; }
.home-tagline span { color: var(--primary-text); font-size: var(--font-page); }

.home-block { position: relative; margin-top: var(--h-over); padding: var(--space-6) 0 var(--space-12); border-radius: var(--h-r) var(--h-r) 0 0; box-shadow: var(--home-band-shadow); }
.home-hello + .home-mark + .home-block { margin-top: 0; }
.home-block-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); padding: 0 var(--space-6) var(--space-3); }
.home-block h2 { font-size: var(--h-26); font-weight: var(--weight-heavy); }
.home-block-head > span { font-size: var(--h-15); color: var(--text-lead); }
.home-block-head a { display: flex; align-items: center; min-height: var(--target-min); margin: calc(-1 * var(--space-3)) calc(-1 * var(--space-2)); padding: 0 var(--space-2); font-size: var(--h-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.home-todo { z-index: 1; background: var(--surface); }
.home-orp { z-index: 2; background: var(--primary-soft); }
.home-offers { z-index: 3; background: var(--peach-soft); padding-bottom: var(--space-8); }
.home-todo.home-stick { position: sticky; top: var(--header-h); }
.home-orp.home-stick { position: sticky; top: calc(var(--header-h) + var(--home-stack-step)); }
.home :is(a, button, [tabindex]) {
  scroll-margin-top: calc(var(--header-h) + var(--home-stack-step) + var(--space-3));
  /* Ni sous la barre de navigation du bas. */
  scroll-margin-bottom: calc(var(--tabbar-h, 0px) + var(--space-3) + env(safe-area-inset-bottom));
}
@media (prefers-reduced-motion: reduce) {
  .home-todo.home-stick, .home-orp.home-stick { position: relative; top: auto; }
}

.home-todo ol { margin: 0 var(--space-6); padding: 0; list-style: none; }
.home-todo li + li { border-top: 1px solid var(--line); }
.home-todo a { display: flex; align-items: center; gap: var(--space-4); min-height: var(--h-row); color: var(--text); text-decoration: none; }
.home-todo-num { flex: none; display: grid; place-items: center; width: var(--h-num); height: var(--h-num); border-radius: 50%; background: var(--surface-muted); color: var(--text); font-size: var(--h-15); font-weight: var(--weight-bold); }
.home-todo-late .home-todo-num { background: var(--peach-text); color: var(--surface); }
.home-todo-text { flex: 1; min-width: 0; padding: var(--space-3) 0; }
.home-todo-text > b { display: block; font-size: var(--h-16); line-height: var(--h-22); font-weight: var(--weight-bold); overflow-wrap: anywhere; }
.home-todo-text > b span { font-weight: var(--weight-semibold); }
.home-todo-text > span { display: block; margin-top: var(--space-1); font-size: var(--h-14); line-height: var(--h-20); color: var(--text-secondary); overflow-wrap: anywhere; }
.home-todo-late .home-todo-text > span { color: var(--peach-text); }
.home-todo :deep(.icon) { flex: none; width: var(--h-20); height: var(--h-20); color: var(--text-secondary); }

.home-orp-bar, .home-orp-none { margin: 0 var(--space-6); }
.home-orp-none { font-weight: var(--weight-bold); }

.tri-peek { position: relative; margin: var(--space-6) var(--space-5) 0; }
.tri-peek-pile { position: absolute; height: var(--h-pile); border-radius: var(--h-pile-r); }
.tri-peek-far { left: var(--h-far); right: var(--h-far); top: var(--h-far-up); background: var(--tri-pile-far); }
.tri-peek-near { left: var(--h-near); right: var(--h-near); top: var(--h-near-up); background: var(--tri-pile-near); }
.tri-peek-card { position: relative; display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4) var(--h-60) var(--space-4) var(--space-4); border: var(--h-3) solid var(--tri-edge); border-radius: var(--h-peek-r); background: var(--surface); }
.tri-peek-card :deep(.logo) { flex: none; width: var(--h-logo); height: var(--h-logo); }
.tri-peek-card > div { flex: 1; min-width: 0; }
.tri-peek-card > div > b { display: block; font-size: var(--h-16); line-height: var(--h-22); font-weight: var(--weight-bold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tri-peek-sub { display: flex; gap: var(--space-1); font-size: var(--h-14); line-height: var(--h-20); color: var(--text-secondary); white-space: nowrap; }
.tri-peek-sub > span:first-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.tri-peek-card span b { font-weight: var(--weight-bold); color: var(--success); }
.tri-peek-card span b.tone-dig { color: var(--score-dig); }
.tri-peek-card span b.tone-far { color: var(--text-secondary); }
.tri-peek-bookmark { position: absolute; right: var(--space-4); top: var(--h-mark-up); }
.home-triage { display: flex; align-items: center; justify-content: center; gap: var(--space-2); min-height: var(--h-btn); margin: var(--space-4) var(--space-5) 0; border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--h-16); font-weight: var(--weight-bold); text-decoration: none; }
.home-triage :deep(.icon) { width: var(--h-18); height: var(--h-18); }
.home-none { margin: var(--space-2) var(--space-5) 0; }
</style>
