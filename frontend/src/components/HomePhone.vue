<script setup lang="ts">
import { companyPlace } from "../format";
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Offer } from "../api/client";
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";
import OrpBar from "./OrpBar.vue";
import ScoreRing from "./ScoreRing.vue";
import TaskCheck from "./TaskCheck.vue";
import TroupeScene from "./TroupeScene.vue";
import { HOME_SCENE } from "../troupe";

// L'Accueil du téléphone, refait d'après la planche AccueilV2 (LISEZMOI du 17.11, §40, §54 et §61 ; mêmes blocs sur
// AccueilJustificatif, AccueilNouveau et AccueilPremiereCandidature) : la scène des 4 personnages (§59), le titre écrit à
// la main, puis quatre feuilles qui s'empilent au défilement : À faire, ORP, Top du jour, N offres à trier. L'ordinateur
// garde sa page (TodayView).
// Le rappel des justificatifs (§57 du 17.11) est chargé à part, seulement quand un mois est à remettre.
const OrpReminder = defineAsyncComponent(() => import("./OrpReminder.vue"));

/** Une ligne de « À faire » : le verbe en gras, le reste, la ligne de détail ; `check` = la tâche faite hors de l'app (§61). */
export type HomeTask = {
  key: string;
  test: string;
  verb: string;
  rest: string;
  detail: string;
  to: RouteLocationRaw;
  tone: "late" | "normal" | "interview";
  check?: boolean;
};
/** Le titre : des lignes à la main (brun, vert ou bleu), sinon un début en texte et une fin à la main. */
export type HomeTitle = { lines: { text: string; tone: "late" | "reached" | "blue" }[]; lead: string; hand: string; sub: string };

const props = defineProps<{
  name: string | null;
  firstDay: boolean;
  month: string;
  count: number;
  target: number | null;
  /** L'échéance ORP du mois (le 5 du mois suivant, reporté au jour ouvrable du canton). */
  due?: string | null;
  pace: boolean;
  week: { count: number; target: number } | null;
  title: HomeTitle;
  tasks: HomeTask[];
  /** Un jour de repos (AccueilV2, état « repos ») : « Si tu veux avancer » à la place de « À faire ». */
  rest: boolean;
  top: Offer[];
  toSort: Offer[];
  /** Les justificatifs cochés comme remis (§61) : la date, jusqu'au prochain chargement. */
  orpDone: string | null;
  orpBusy: boolean;
  /** Le rappel des justificatifs à remettre (§57 du 17.11) : posé seulement quand un mois est à remettre. */
  reminder?: { month: string; due: string; late: boolean; to: RouteLocationRaw } | null;
}>();
const emit = defineEmits<{ "orp-check": [checked: boolean] }>();

// La raison de la ligne « à trier » : une compétence demandée par l'annonce et présente dans le profil, surlignée
// comme les mots de l'annonce (<mark>).
function reason(offer: Offer): string | null {
  return offer.keywords_asks.find((k) => k.covered)?.text ?? null;
}
// Comme avant : la ville seule, sans le canton (« Acme SA · Lausanne »).
function where(offer: Offer): string {
  return companyPlace(offer.company, offer.location, true);
}
const sortTitle = computed(() => (props.toSort.length === 1 ? "1 offre à trier" : `${props.toSort.length} offres à trier`));
const sortRows = computed(() => props.toSort.slice(0, 3));
function taskDetail(task: HomeTask): string {
  return task.check && props.orpDone ? `Remis ${dateInSentence(props.orpDone)}` : task.detail;
}

// Les feuilles empilées au défilement (§54 du 17.11) : chacune colle 56 px sous la précédente (sous la barre du logo,
// --header-h) et la suivante glisse par-dessus ; une feuille recouverte garde son titre en haut, réduit de 26 à 18 px.
// - une feuille ne colle que si elle tient dans la hauteur visible (sinon ses dernières lignes ne se verraient jamais) ;
// - toucher le titre d'une feuille recouverte, ou y amener le focus, fait défiler jusqu'à elle (d'un coup si les
//   animations sont réduites).
type Sheet = "todo" | "orp" | "top" | "sort";
const ORDER: Sheet[] = ["todo", "orp", "top", "sort"];
const sheets = reactive<Record<Sheet, HTMLElement | null>>({ todo: null, orp: null, top: null, sort: null });
const sticks = reactive<Record<Sheet, boolean>>({ todo: false, orp: false, top: false, sort: false });
const covered = reactive<Record<Sheet, boolean>>({ todo: false, orp: false, top: false, sort: false });
const reduced = () => typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const headerHeight = () => document.querySelector(".topbar")?.getBoundingClientRect().height ?? 0;
const present = () => ORDER.filter((key) => sheets[key]);
// La place de chaque feuille dans la pile : 0, 1, 2, 3 (les feuilles absentes ne comptent pas).
const rank = computed(() => {
  const list = ORDER.filter((key) => (key === "todo" ? props.tasks.length : key === "top" ? props.top.length : key === "sort" ? props.toSort.length : true));
  return Object.fromEntries(list.map((key, i) => [key, i])) as Partial<Record<Sheet, number>>;
});
const setSheet = (key: Sheet) => (el: unknown) => {
  sheets[key] = (el as HTMLElement | null) ?? null;
};

function measure(): void {
  const visible = window.innerHeight - headerHeight();
  for (const key of ORDER) {
    const el = sheets[key];
    sticks[key] = Boolean(el) && el!.offsetHeight <= visible - (rank.value[key] ?? 0) * 56;
  }
  update();
}
// Recouverte : la feuille suivante est arrivée sur son bord du haut (à 56 px près, la hauteur d'un titre empilé).
function update(): void {
  const list = present();
  list.forEach((key, i) => {
    const el = sheets[key], next = list[i + 1] ? sheets[list[i + 1]!] : null;
    covered[key] = Boolean(sticks[key] && el && next) && next!.getBoundingClientRect().top < el!.getBoundingClientRect().top + 57;
  });
}
let frame = 0;
function onScroll(): void {
  if (frame) return;
  frame = requestAnimationFrame(() => {
    frame = 0;
    update();
  });
}
function scrollToSheet(key: Sheet): void {
  const el = sheets[key];
  if (!el) return;
  // La place de la feuille dans le flux : son haut sans la colle, moins le chevauchement et l'endroit où elle colle.
  const stuck = el.style.position;
  el.style.position = "relative";
  const top = el.getBoundingClientRect().top + window.scrollY - headerHeight() - (rank.value[key] ?? 0) * 56;
  el.style.position = stuck;
  window.scrollTo({ top, behavior: reduced() ? "auto" : "smooth" });
}
function onSheetClick(key: Sheet, event: MouseEvent): void {
  if (!covered[key]) return;
  event.preventDefault();
  event.stopPropagation();
  scrollToSheet(key);
}
// Clavier (WCAG 2.4.11) : un élément qui prend le focus dans une feuille recouverte n'y reste pas caché.
function onSheetFocus(key: Sheet): void {
  if (covered[key]) scrollToSheet(key);
}

let observer: ResizeObserver | null = null;
onMounted(() => {
  measure();
  window.addEventListener("resize", measure);
  window.addEventListener("scroll", onScroll, { passive: true });
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(measure);
    for (const el of Object.values(sheets)) if (el) observer.observe(el);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", measure);
  window.removeEventListener("scroll", onScroll);
  if (frame) cancelAnimationFrame(frame);
  observer?.disconnect();
});
const sheetClass = (key: Sheet) => ["home-sheet", `home-${key}`, { "home-stick": sticks[key], "home-covered": covered[key] }];
const sheetStyle = (key: Sheet) => ({ "--home-rank": String(rank.value[key] ?? 0) });
</script>

<template>
  <div
    class="home"
    data-test="home-phone"
  >
    <OrpReminder
      v-if="reminder"
      v-bind="reminder"
    />
    <div class="home-hello">
      <!-- La scène des 4 personnages (§59 du 17.11) : centrée au-dessus du titre, 110 px de haut. -->
      <TroupeScene
        :scene="HOME_SCENE"
        :height="110"
        full
      />
      <!-- Le titre à la main (AccueilV2) : 25 px, penché de 2°, brun pour le retard, vert pour l'objectif atteint, bleu
           pour la suite ; la phrase de 15/22 dessous. -->
      <h1
        v-if="title.lines.length"
        class="home-hand"
        data-test="home-title"
      >
        <template
          v-for="(line, i) in title.lines"
          :key="i"
        >
          <br v-if="i"><span :class="`home-hand-${line.tone}`">{{ line.text }}</span>
        </template>
      </h1>
      <h1
        v-else
        class="home-lead"
        data-test="home-title"
      >
        {{ title.lead || `Bonjour${name ? ` ${name}` : ""}.` }}<template v-if="title.lead && title.hand">
          {{ " " }}<span class="home-hand-blue">{{ title.hand }}</span>
        </template>
      </h1>
      <p
        v-if="title.sub"
        class="home-sub"
        data-test="home-sub"
      >
        {{ title.sub }}
      </p>
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
      v-if="tasks.length"
      :ref="setSheet('todo')"
      :class="sheetClass('todo')"
      :style="sheetStyle('todo')"
      aria-labelledby="home-todo-title"
      data-test="home-todo"
      @click.capture="onSheetClick('todo', $event)"
      @focusin="onSheetFocus('todo')"
    >
      <div class="home-head">
        <h2 id="home-todo-title">
          {{ rest ? "Si tu veux avancer" : "À faire" }}
        </h2>
      </div>
      <ul class="home-rows">
        <li
          v-for="(task, i) in tasks"
          :key="task.key"
          :class="{ 'home-checkable': task.check }"
        >
          <!-- La tâche faite hors de l'app se coche (§61) : le cercle orange à la place du numéro, à côté du lien. -->
          <TaskCheck
            v-if="task.check"
            :checked="!!orpDone"
            :label="orpDone ? `Annuler : ${task.rest} pas encore remis` : `Marquer comme remis : ${task.rest}`"
            tone="late"
            :busy="orpBusy"
            data-test="home-orp-check"
            @toggle="emit('orp-check', $event)"
          />
          <RouterLink
            :to="task.to"
            class="home-row home-task"
            :data-test="`todo-${task.test}`"
          >
            <span
              v-if="task.check"
              class="home-num home-num-check"
              aria-hidden="true"
            />
            <b
              v-else
              class="home-num"
              aria-hidden="true"
            >{{ i + 1 }}</b>
            <span class="home-row-main">
              <b>{{ task.verb }} <span>{{ task.rest }}</span></b>
              <span :class="['home-row-sub', { 'home-row-late': task.tone === 'late' && !(task.check && orpDone) }]">{{ taskDetail(task) }}</span>
            </span>
            <AppIcon name="chevron" />
          </RouterLink>
        </li>
      </ul>
    </section>

    <section
      :ref="setSheet('orp')"
      :class="sheetClass('orp')"
      :style="sheetStyle('orp')"
      aria-labelledby="home-orp-title"
      data-test="home-band-orp"
      @click.capture="onSheetClick('orp', $event)"
      @focusin="onSheetFocus('orp')"
    >
      <div class="home-head">
        <h2 id="home-orp-title">
          ORP
        </h2>
        <RouterLink
          to="/bilan/orp"
          data-test="home-orp"
        >
          Voir le suivi
        </RouterLink>
      </div>
      <div class="home-orp-bar">
        <OrpBar
          :month="month"
          :count="count"
          :target="target"
          :due="due ?? null"
          :pace="pace"
          :week="week"
        />
      </div>
    </section>

    <section
      v-if="top.length"
      :ref="setSheet('top')"
      :class="sheetClass('top')"
      :style="sheetStyle('top')"
      aria-labelledby="home-top-title"
      data-test="home-top"
      @click.capture="onSheetClick('top', $event)"
      @focusin="onSheetFocus('top')"
    >
      <div class="home-head">
        <h2 id="home-top-title">
          Top du jour
        </h2>
        <RouterLink
          :to="{ path: '/candidatures/offres' }"
          data-test="home-offers-all"
        >
          Tout voir
        </RouterLink>
      </div>
      <ul class="home-rows">
        <li
          v-for="offer in top"
          :key="offer.id"
        >
          <RouterLink
            :to="{ path: '/candidatures/offres', query: { offre: String(offer.id) } }"
            class="home-row home-offer"
            data-test="home-top-offer"
          >
            <span class="home-row-main">
              <b>{{ offer.title }}</b>
              <span class="home-row-sub">{{ where(offer) }}</span>
            </span>
            <ScoreRing
              :score="offer.score ?? null"
              bare
            />
            <AppIcon name="chevron" />
          </RouterLink>
        </li>
      </ul>
    </section>

    <section
      v-if="toSort.length"
      :ref="setSheet('sort')"
      :class="sheetClass('sort')"
      :style="sheetStyle('sort')"
      aria-labelledby="home-sort-title"
      data-test="home-band-offers"
      @click.capture="onSheetClick('sort', $event)"
      @focusin="onSheetFocus('sort')"
    >
      <div class="home-head">
        <h2 id="home-sort-title">
          {{ sortTitle }}
        </h2>
        <span class="home-head-note">Pas encore vues</span>
      </div>
      <ul class="home-rows">
        <li
          v-for="offer in sortRows"
          :key="offer.id"
        >
          <RouterLink
            :to="{ path: '/candidatures/offres', query: { offre: String(offer.id) } }"
            class="home-row home-offer"
            data-test="home-card"
          >
            <span
              class="home-dot"
              role="img"
              aria-label="Pas encore vue"
            />
            <span class="home-row-main">
              <b>{{ offer.title }}</b>
              <span class="home-row-sub home-row-why"><span class="home-row-cut">{{ where(offer) }}{{ where(offer) && reason(offer) ? " ·" : "" }}</span><mark v-if="reason(offer)">{{ reason(offer) }}</mark></span>
            </span>
            <ScoreRing
              :score="offer.score ?? null"
              bare
            />
            <AppIcon name="chevron" />
          </RouterLink>
        </li>
      </ul>
      <RouterLink
        :to="{ name: 'triage' }"
        class="home-sort-go"
        data-test="home-triage"
      >
        Trier les offres<AppIcon name="arrow-right" />
      </RouterLink>
    </section>
  </div>
</template>

<style>
/* Les styles de l'Accueil du téléphone, chargés avec lui : l'ordinateur ne les reçoit pas. Valeurs de la planche
   AccueilV2 (+ Sombre), LISEZMOI du 17.11, §40 et §54. */
.home {
  --home-sheet-white: var(--surface);
  --home-sheet-orp: var(--primary-soft);
  --home-sheet-top: var(--success-soft);
  --home-sheet-sort: #FCEDE4;
  --home-rule-top: #C5E3D2;
  --home-rule-sort: #F1D3C0;
  --home-mark: #FFE9A8;
  --home-hand-late: #8A4A12;
  /* Valeurs de la planche AccueilV2 hors échelle : nommées ici (garde-fou docs/135). */
  --home-10: 0.625rem;
  --home-14: 0.875rem;
  --home-40: 2.5rem;
  --home-44: 2.75rem;
  --home-hand-size: 1.5625rem;
  --home-lap: 1.75rem; /* chevauchement des feuilles */
  --home-lh-sub: 1.4667;
  --home-lh-22: 1.375rem;
  --home-lh-20: 1.25rem;
  --home-2: 0.125rem;
  --home-6: 0.375rem;
  --home-step: 3.5rem; /* 56 px : la place d'un titre empilé */
  --home-shadow: 0 -6px 16px rgb(27 31 42 / 6%);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .home { --home-sheet-sort: #2E231B; --home-rule-top: #2C4A39; --home-rule-sort: #4A3628; --home-mark: #5A4A1E; --home-hand-late: var(--peach-text); }
}
:root[data-theme="dark"] .home { --home-sheet-sort: #2E231B; --home-rule-top: #2C4A39; --home-rule-sort: #4A3628; --home-mark: #5A4A1E; --home-hand-late: var(--peach-text); }

.home h1, .home h2 { margin: 0; letter-spacing: -0.03em; line-height: var(--leading-none); }
.home-hello { display: grid; gap: var(--home-10); padding: 0 var(--space-6) var(--home-40); }
.home-hello > .troupe { justify-self: center; }
/* Le titre à la main : 25 px, penché de 2°. */
.home-hand { font-size: var(--home-hand-size); font-weight: var(--weight-regular); letter-spacing: 0; }
.home-hand span { display: inline-block; font-family: var(--font-hand); line-height: var(--leading-none); transform: rotate(-2deg); }
.home-hand-late { color: var(--home-hand-late); }
.home-hand-reached { color: var(--success); }
.home-hand-blue { color: var(--primary-text); }
.home-lead { font-size: var(--title-hello); font-weight: var(--weight-bold); }
.home-lead .home-hand-blue { font-family: var(--font-hand); font-weight: var(--weight-regular); letter-spacing: 0; }
.home-sub { margin: var(--space-2) 0 0; font-size: var(--font-label); line-height: var(--home-lh-sub); color: var(--text-lead); }
.home-tagline { margin: 0; font-size: var(--font-section); font-weight: var(--weight-bold); color: var(--text-tertiary); }
.home-tagline s { text-decoration: line-through wavy var(--scribble) 3px; }
.home-tagline span { color: var(--primary-text); font-size: var(--font-page); }

/* Les feuilles : rayon 32 en haut, 24 px au-dessus du titre, 48 dessous ; chacune remonte de 28 px sur la précédente. */
.home-sheet { position: relative; z-index: calc(1 + var(--home-rank)); margin-top: calc(-1 * var(--home-lap)); padding: var(--space-6) 0 var(--space-12); border-radius: var(--space-8) var(--space-8) 0 0; box-shadow: var(--home-shadow); }
.home-sheet:first-of-type, .home-hello + .home-sheet { margin-top: 0; }
.home-todo { --home-bg: var(--home-sheet-white); }
.home-orp { --home-bg: var(--home-sheet-orp); }
.home-top { --home-bg: var(--home-sheet-top); padding-bottom: var(--home-44); }
.home-sort { --home-bg: var(--home-sheet-sort); }
.home-sheet { background: var(--home-bg); }
/* La dernière feuille descend jusqu'à la barre du bas (la planche n'a pas de fond de page sous elle). */
.home-sheet:last-child { box-shadow: var(--home-shadow), 0 16rem 0 0 var(--home-bg); }
/* §54 : collée sous la barre du logo, 56 px sous la précédente ; seulement si elle tient dans l'écran (.home-stick). */
.home-sheet.home-stick { position: sticky; top: calc(var(--header-h) + var(--home-rank) * var(--home-step)); }
.home-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); padding: 0 var(--space-6) var(--space-3); }
.home-top .home-head, .home-sort .home-head { padding-bottom: var(--home-6); }
.home-head h2 { font-size: var(--font-figure); font-weight: var(--weight-heavy); transition: font-size var(--t-standard, 0.2s) var(--ease-standard, ease); }
/* Recouverte : le titre passe de 26 à 18 px pour garder de la place sur les petits écrans. */
.home-covered .home-head h2 { font-size: var(--font-title); }
.home-head a { display: flex; align-items: center; min-height: var(--target-min); margin: calc(-1 * var(--space-3)) 0; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.home-head-note { font-size: var(--font-label); color: var(--text-secondary); }
@media (prefers-reduced-motion: reduce) { .home-head h2 { transition: none; } }

.home-rows { margin: 0; padding: 0; list-style: none; }
.home-rows li { margin: 0 var(--space-6); }
.home-rows li + li { border-top: 1px solid var(--line); }
.home-top .home-rows li + li { border-top-color: var(--home-rule-top); }
.home-sort .home-rows li + li { border-top-color: var(--home-rule-sort); }
.home-row { display: flex; align-items: center; gap: var(--space-4); min-height: 4.5rem; color: var(--text); text-decoration: none; }
.home-offer { gap: var(--home-14); min-height: 4.25rem; }
.home-sort .home-offer { gap: var(--space-3); }
.home-row-main { flex: 1; min-width: 0; }
.home-row-main > b { display: block; font-size: var(--font-body); line-height: var(--home-lh-22); font-weight: var(--weight-bold); }
.home-row-main > b > span { font-weight: var(--weight-semibold); }
.home-offer .home-row-main > b, .home-row-cut { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
/* « entreprise · lieu · » se coupe, la raison surlignée reste entière. */
.home-row-sub.home-row-why { display: flex; gap: var(--space-1); min-width: 0; }
.home-row-why mark { flex: none; max-width: 60%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.home-row-sub { display: block; margin-top: var(--home-2); font-size: var(--font-small); line-height: var(--home-lh-20); color: var(--text-lead); }
.home-task .home-row-sub { margin-top: var(--space-1); color: var(--text-secondary); }
.home-task .home-row-sub.home-row-late { color: var(--home-hand-late); }
.home-sort .home-row-sub { color: var(--text-secondary); }
.home-row-sub mark { padding: 0 var(--space-1); border-radius: var(--radius-sm); background: var(--home-mark); color: var(--text); }
.home-row > .icon { flex: none; color: var(--text-lead); }
/* La note : 44 px, toujours à la même place. Sans le « padding: 0 », la règle globale « .close » (bouton Fermer)
   décalait de 8 px les notes « Proche ». */
.home-offer .score-ring-wrap { flex: none; width: 2.75rem; padding: 0; }
.home-offer .score-ring { width: 2.75rem; height: 2.75rem; }
.home-top .home-row-sub { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
/* Le numéro : rond de 32 px gris, 15 px gras. */
.home-num { flex: none; display: grid; place-items: center; width: var(--space-8); height: var(--space-8); border-radius: 50%; background: var(--surface-muted); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.home-num-check { background: none; }
/* §61 : le cercle à cocher (26 px, zone de 44) posé sur la place du numéro ; le lien garde toute la ligne. */
.home-checkable { position: relative; }
.home-checkable > .task-check { position: absolute; z-index: 1; top: 50%; left: -0.375rem; transform: translateY(-50%); }
.home-orp-bar { padding: 0 var(--space-6); }
.home-dot { flex: none; width: 0.625rem; height: 0.625rem; border-radius: 50%; background: var(--action); }
.home-sort-go { display: flex; align-items: center; justify-content: center; gap: var(--space-2); height: var(--space-12); margin: var(--space-3) var(--space-5) 0; border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none; }
.home-sort-go .icon { width: 1.125rem; height: 1.125rem; }
.home :is(a, button, [tabindex]) {
  scroll-margin-top: calc(var(--header-h) + 4 * var(--home-step));
  scroll-margin-bottom: calc(var(--tabbar-h, 0px) + var(--space-3) + env(safe-area-inset-bottom));
}
</style>
