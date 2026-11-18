<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { api, type OrpMonth } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import { usePageReady } from "../composables/usePageTransition";
import { formatMonth, orpLeftLine, shiftMonth } from "../format";

// Le Bilan sur téléphone (LISEZMOI du 17.11, §52 et §54 ; planches BilanAccueil et BilanAccueilSombre) : trois
// feuilles empilées, ORP, Résultats et Formations, chacune avec son lien vers la page de détail. Au défilement,
// chaque feuille reste collée (top 0, 64, 128 px) et la suivante glisse par-dessus ; le titre d'une feuille
// recouverte passe de 26 à 18 px, et le toucher ramène à sa feuille. Les chiffres viennent des appels existants
// (/api/orp, /api/insights, /api/trainings) : rien de nouveau côté serveur.
type Insights = components["schemas"]["SearchReportOut"];
type Training = components["schemas"]["TrainingOut"];

const ORP_DETAIL = { path: "/bilan", query: { vue: "orp" } };
const current = ref<OrpMonth | null>(null);
const previous = ref<OrpMonth | null>(null);
const insights = ref<Insights | null>(null);
const training = ref<Training | null>(null);
const loaded = ref(false);
const failed = ref(false);
usePageReady("bilan-orp", () => loaded.value || failed.value);

function thisMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}
const monthName = (month: string): string => formatMonth(month).split(" ")[0]!.toLowerCase();

// ORP : la barre du mois, la ligne « Encore 3 d'ici le 5 décembre · 3 à déclarer », et la pastille du mois passé
// dont les justificatifs restent à remettre.
const orpTitle = computed(() => `Mois ORP · ${monthName(current.value?.month ?? thisMonth())}`);
const orpCount = computed(() => (current.value?.target ? `${current.value.count} sur ${current.value.target}` : ""));
const orpWidth = computed(() => {
  const o = current.value;
  return o?.target ? `${Math.min(100, Math.round((o.count / o.target) * 100))}%` : "0%";
});
const toDeclare = computed(
  () =>
    [previous.value, current.value]
      .filter((m): m is OrpMonth => !!m && m.state !== "remis")
      .flatMap((m) => m.rows)
      .filter((row) => !row.declared_at).length,
);
const orpLine = computed(() => {
  const o = current.value;
  if (!o) return "";
  const left = o.target ? orpLeftLine(o.count, o.target, o.month, o.due_date) : "Indique l’objectif fixé avec ton ORP dans les Réglages";
  return toDeclare.value ? `${left} · ${toDeclare.value} à déclarer` : left;
});
const lateMonth = computed(() => {
  const p = previous.value;
  if (p?.state !== "a_remettre") return "";
  const name = monthName(p.month);
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} à remettre`;
});

// Résultats, depuis le début : Envoyées, Réponses, Entretiens, chacune sur la barre des envoyées.
const funnel = computed(() => {
  const f = insights.value?.funnel;
  const max = Math.max(f?.applications ?? 0, 1);
  return [
    { key: "applications", label: "Envoyées", value: f?.applications ?? 0 },
    { key: "responses", label: "Réponses", value: f?.responses ?? 0 },
    { key: "interviews", label: "Entretiens", value: f?.interviews ?? 0 },
  ].map((row) => ({ ...row, width: `${Math.round((row.value / max) * 100)}%` }));
});
// « 1 réponse sur 5 » : une réponse pour combien de candidatures envoyées, arrondi.
const ratio = computed(() => {
  const f = insights.value?.funnel;
  return f && f.responses > 0 ? `1 réponse sur ${Math.max(1, Math.round(f.applications / f.responses))}` : "";
});

// Formations : la formation en cours (la première), son module et sa barre.
const trainingModule = computed(() => {
  const m = training.value?.mark;
  return m?.modules_total ? `Module ${m.modules_done ?? 0} sur ${m.modules_total}` : "";
});
const trainingWidth = computed(() => {
  const m = training.value?.mark;
  return m?.modules_total ? `${Math.round(((m.modules_done ?? 0) / m.modules_total) * 100)}%` : "0%";
});

async function load(): Promise<void> {
  failed.value = false;
  try {
    const month = thisMonth();
    const [orp, prev, ins, trainings] = await Promise.all([
      api.GET("/api/orp"),
      api.GET("/api/orp", { params: { query: { month: shiftMonth(month, -1) } } }),
      api.GET("/api/insights", { params: { query: { period: "all" } } }),
      api.GET("/api/trainings", { params: { query: { domain_only: false } } }),
    ]);
    if (!orp.data || !ins.data) throw new Error();
    current.value = orp.data;
    previous.value = prev.data ?? null;
    insights.value = ins.data;
    training.value = trainings.data?.items.find((t) => t.mark?.status === "in_progress") ?? null;
    loaded.value = true;
  } catch {
    failed.value = true;
  }
}

// §54 : une feuille est recouverte quand la suivante est collée à sa place (sous la barre du haut, puis 64 et 128 px
// plus bas). Le `top` de chaque feuille vient du CSS.
const stick = (el: HTMLElement | undefined): number => (el ? parseFloat(getComputedStyle(el).top) || 0 : 0);
const sheets = ref<HTMLElement[]>([]);
const covered = ref([false, false, false]);
let frame = 0;
function measure(): void {
  frame = 0;
  const next = sheets.value.map((sheet, i) => {
    const after = sheets.value[i + 1];
    return !!after && after.getBoundingClientRect().top <= stick(after) + 1 && sheet.getBoundingClientRect().top <= stick(sheet) + 1;
  });
  if (next.some((v, i) => v !== covered.value[i])) covered.value = next;
}
function onScroll(): void {
  if (!frame) frame = requestAnimationFrame(measure);
}
// Toucher un titre empilé : la page défile jusqu'à sa feuille (sa place dans le fil, sous les précédentes).
function reveal(i: number): void {
  if (!covered.value[i]) return;
  const first = sheets.value[0];
  if (!first) return;
  // Les feuilles ne changent pas de hauteur en se collant : la place d'une feuille est la somme des précédentes,
  // moins leur chevauchement de 28 px.
  const overlap = 28;
  let top = first.parentElement!.getBoundingClientRect().top + globalThis.scrollY;
  for (let k = 0; k < i; k += 1) top += sheets.value[k]!.offsetHeight - overlap;
  const reduce = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  globalThis.scrollTo({ top: top - stick(sheets.value[i]), behavior: reduce ? "auto" : "smooth" });
}
onMounted(() => {
  void load();
  globalThis.addEventListener("scroll", onScroll, { passive: true });
  measure();
});
onUnmounted(() => {
  globalThis.removeEventListener("scroll", onScroll);
  if (frame) cancelAnimationFrame(frame);
});
</script>

<template>
  <div
    class="bilan-stack"
    data-test="bilan-stack"
  >
    <section
      :ref="(el) => (sheets[0] = el as HTMLElement)"
      :class="['bilan-sheet', 'bilan-sheet-orp', { covered: covered[0] }]"
      aria-labelledby="bilan-sheet-orp"
      data-test="bilan-sheet-orp"
    >
      <div class="bilan-sheet-head">
        <span class="bilan-sheet-name">
          <h2 id="bilan-sheet-orp">
            <button
              type="button"
              class="bilan-sheet-title"
              :tabindex="covered[0] ? 0 : -1"
              @click="reveal(0)"
            >ORP</button>
          </h2>
          <RouterLink
            v-if="lateMonth"
            :to="ORP_DETAIL"
            class="bilan-sheet-late"
            data-test="bilan-orp-late"
          ><AppIcon name="alert-circle" />{{ lateMonth }}</RouterLink>
        </span>
        <RouterLink
          :to="ORP_DETAIL"
          class="bilan-sheet-link"
          data-test="bilan-orp-link"
        >Voir le suivi</RouterLink>
      </div>
      <div class="bilan-sheet-body">
        <p
          v-if="failed"
          class="bilan-sheet-line"
        >
          Bilan indisponible pour l’instant.
        </p>
        <template v-else>
          <div class="bilan-sheet-row">
            <b>{{ orpTitle }}</b><b data-test="bilan-orp-count">{{ orpCount }}</b>
          </div>
          <div class="bilan-sheet-bar">
            <i :style="{ width: orpWidth }" />
          </div>
          <p
            class="bilan-sheet-line"
            data-test="bilan-orp-line"
          >
            {{ orpLine }}
          </p>
        </template>
      </div>
    </section>
    <section
      :ref="(el) => (sheets[1] = el as HTMLElement)"
      :class="['bilan-sheet', 'bilan-sheet-results', { covered: covered[1] }]"
      aria-labelledby="bilan-sheet-results"
      data-test="bilan-sheet-results"
    >
      <div class="bilan-sheet-head">
        <h2 id="bilan-sheet-results">
          <button
            type="button"
            class="bilan-sheet-title"
            :tabindex="covered[1] ? 0 : -1"
            @click="reveal(1)"
          >
            Résultats
          </button>
        </h2>
        <RouterLink
          to="/bilan/resultats"
          class="bilan-sheet-link"
          data-test="bilan-results-link"
        >Voir le détail</RouterLink>
      </div>
      <div class="bilan-sheet-body bilan-funnel-rows">
        <div
          v-for="row in funnel"
          :key="row.key"
          class="bilan-funnel-row"
          :data-test="`bilan-funnel-${row.key}`"
        >
          <span>{{ row.label }}</span>
          <span class="bilan-sheet-bar"><i :style="{ width: row.width }" /></span>
          <b>{{ loaded ? row.value : "" }}</b>
        </div>
        <div class="bilan-sheet-ratio">
          <span
            v-if="ratio"
            class="bilan-sheet-pill"
            data-test="bilan-ratio"
          >{{ ratio }}</span>
          <span>depuis le début</span>
        </div>
      </div>
    </section>
    <section
      :ref="(el) => (sheets[2] = el as HTMLElement)"
      :class="['bilan-sheet', 'bilan-sheet-trainings', { covered: covered[2] }]"
      aria-labelledby="bilan-sheet-trainings"
      data-test="bilan-sheet-trainings"
    >
      <div class="bilan-sheet-head">
        <h2 id="bilan-sheet-trainings">
          <button
            type="button"
            class="bilan-sheet-title"
            :tabindex="covered[2] ? 0 : -1"
            @click="reveal(2)"
          >
            Formations
          </button>
        </h2>
        <RouterLink
          to="/bilan/formations"
          class="bilan-sheet-link"
          data-test="bilan-trainings-link"
        >Catalogue</RouterLink>
      </div>
      <div class="bilan-sheet-body">
        <template v-if="training">
          <div class="bilan-sheet-row">
            <b class="bilan-sheet-ellipsis">{{ training.title }}</b><span>{{ trainingModule }}</span>
          </div>
          <div class="bilan-sheet-bar">
            <i :style="{ width: trainingWidth }" />
          </div>
        </template>
        <p class="bilan-sheet-line">
          L’ORP peut financer une formation
        </p>
      </div>
    </section>
  </div>
</template>

<style>
/* Planches BilanAccueil et BilanAccueilSombre (§52) ; collées au défilement (§54). */
.bilan-stack {
  --sheet-orp: #E8ECFB; --sheet-results: #E3F3EA; --sheet-trainings: #EFE9F7;
  --sheet-orp-fill: #2445C2; --sheet-results-fill: #17734A; --sheet-trainings-fill: #5B3E8C;
  --sheet-track: #FFFFFF; --sheet-results-track: rgb(23 115 74 / 14%); --sheet-text: #3D4250; --sheet-link: #1A3496;
  --sheet-late-bg: #FDF0E2; --sheet-late-text: #8A4A16; --sheet-pill: #FFFFFF;
  --sheet-overlap: -28px; --sheet-bar: 10px; --sheet-pill-h: 28px; --sheet-title: 26px; --sheet-title-lh: 32px; --sheet-13: 13px; --sheet-lh-22: 22px; --sheet-lh-20: 20px;
  display: flex; flex-direction: column;
}
/* La première feuille commence juste sous la barre du logo (planche BilanAccueil) : l'en-tête de la page, sans onglets,
   ne garde que son titre pour les lecteurs d'écran. */
.page-head:has(+ .bilan-stack) { padding: 0; }
.page-head:has(+ .bilan-stack) h1 { margin: 0; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .bilan-stack {
    --sheet-orp: #232B45; --sheet-results: #1F3A2C; --sheet-trainings: #2A2338;
    --sheet-orp-fill: #7D95FF; --sheet-results-fill: #62D497; --sheet-trainings-fill: #B9A2E8;
    --sheet-track: #221E1A; --sheet-results-track: #221E1A; --sheet-text: #D9D2C7; --sheet-link: #AEBDFF;
    --sheet-late-bg: #3A281E; --sheet-late-text: #F2B98E; --sheet-pill: #221E1A;
  }
}
:root[data-theme="dark"] .bilan-stack {
  --sheet-orp: #232B45; --sheet-results: #1F3A2C; --sheet-trainings: #2A2338;
  --sheet-orp-fill: #7D95FF; --sheet-results-fill: #62D497; --sheet-trainings-fill: #B9A2E8;
  --sheet-track: #221E1A; --sheet-results-track: #221E1A; --sheet-text: #D9D2C7; --sheet-link: #AEBDFF;
  --sheet-late-bg: #3A281E; --sheet-late-text: #F2B98E; --sheet-pill: #221E1A;
}
.bilan-sheet {
  position: sticky; top: var(--header-h); z-index: 1; padding: var(--space-6) 0 var(--space-12);
  border-radius: var(--space-8) var(--space-8) 0 0; background: var(--sheet-orp); box-shadow: 0 -6px 16px rgb(27 31 42 / 6%);
}
.bilan-sheet + .bilan-sheet { margin-top: var(--sheet-overlap); }
.bilan-sheet-results { top: calc(var(--header-h) + 64px); z-index: 2; background: var(--sheet-results); }
/* La dernière feuille va jusqu'en bas de la page, sous la barre du bas, et remplit l'écran : les trois peuvent
   s'empiler en haut, et rien ne les pousse au bout du défilement (la page n'a plus de marge sous les feuilles). */
.bilan-sheet-trainings {
  top: calc(var(--header-h) + 128px); z-index: 3; min-height: calc(100dvh - var(--header-h) - 128px); background: var(--sheet-trainings);
  padding-bottom: calc(var(--tabbar-h) + var(--space-12) + env(safe-area-inset-bottom));
}
:root:has(.bilan-stack) main { padding-bottom: 0; }
.bilan-sheet-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); padding: 0 var(--space-6) var(--space-3); }
.bilan-sheet-orp .bilan-sheet-head { margin-bottom: var(--space-3); }
/* Sous 360 px, la pastille passe sous le titre plutôt que de chevaucher « Voir le suivi ». */
.bilan-sheet-name { display: flex; flex: 1; flex-wrap: wrap; align-items: center; gap: var(--space-1) var(--space-3); min-width: 0; }
.bilan-sheet h2 { margin: 0; font-size: var(--sheet-title); line-height: var(--sheet-title-lh); font-weight: var(--weight-heavy); transition: font-size 0.2s cubic-bezier(0.2, 0, 0, 1); }
/* §54 : recouverte, le titre passe à 18 px ; la hauteur de sa ligne ne change pas, rien ne saute. */
.bilan-sheet.covered h2 { font-size: var(--font-title); }
.bilan-sheet-title { all: unset; position: relative; cursor: pointer; }
/* La zone de toucher fait 44 px : 6 px au-dessus et au-dessous de la ligne de 32 px. */
.bilan-sheet-title::before { content: ""; position: absolute; inset: calc((var(--target-min) - var(--sheet-title-lh)) / -2) 0; }
.bilan-sheet-title:focus-visible { outline: 2px solid var(--focus, var(--primary)); outline-offset: 2px; border-radius: var(--space-1); }
.bilan-sheet-link { display: inline-flex; flex: none; align-items: center; min-height: var(--target-min); color: var(--sheet-link); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; }
.bilan-sheet-late {
  display: inline-flex; align-items: center; gap: var(--space-1); height: var(--sheet-pill-h); padding: 0 var(--space-3); border-radius: var(--radius-pill);
  background: var(--sheet-late-bg); color: var(--sheet-late-text); font-size: var(--sheet-13); font-weight: var(--weight-bold); text-decoration: none; white-space: nowrap;
}
.bilan-sheet-late > .icon { width: 15px; height: 15px; }
.bilan-sheet-body { padding: 0 var(--space-6); }
.bilan-sheet-row { display: flex; justify-content: space-between; gap: var(--space-3); font-size: var(--font-body); line-height: var(--sheet-lh-22); }
.bilan-sheet-row > span { flex: none; font-size: var(--font-small); }
.bilan-sheet-ellipsis { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bilan-sheet-bar { display: block; height: var(--sheet-bar); margin-top: var(--space-2); overflow: hidden; border-radius: var(--radius-pill); background: var(--sheet-track); }
.bilan-sheet-bar > i { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--sheet-orp-fill); transition: width 0.4s cubic-bezier(0.2, 0, 0, 1); }
.bilan-sheet-trainings .bilan-sheet-bar > i { background: var(--sheet-trainings-fill); }
.bilan-sheet-line { margin: var(--space-2) 0 0; color: var(--sheet-text); font-size: var(--font-small); line-height: var(--sheet-lh-20); }
.bilan-funnel-rows { display: flex; flex-direction: column; gap: var(--space-2); }
.bilan-funnel-row { display: grid; grid-template-columns: 92px 1fr 40px; align-items: center; gap: var(--space-3); height: 30px; }
.bilan-funnel-row > span:first-child { color: var(--sheet-text); font-size: var(--font-label); }
.bilan-funnel-row .bilan-sheet-bar { margin: 0; background: var(--sheet-results-track); }
.bilan-funnel-row .bilan-sheet-bar > i { background: var(--sheet-results-fill); }
.bilan-funnel-row > b { font-size: var(--font-title); font-weight: var(--weight-heavy); text-align: right; font-variant-numeric: tabular-nums; }
.bilan-sheet-ratio { display: flex; margin-top: var(--space-1); flex-wrap: wrap; align-items: center; gap: var(--space-2); min-height: var(--sheet-pill-h); color: var(--sheet-text); font-size: var(--font-small); }
.bilan-sheet-pill { display: inline-flex; align-items: center; height: var(--sheet-pill-h); padding: 0 var(--space-3); border-radius: var(--radius-pill); background: var(--sheet-pill); color: var(--sheet-results-fill); font-size: var(--sheet-13); font-weight: var(--weight-bold); }
@media (prefers-reduced-motion: reduce) { .bilan-sheet h2, .bilan-sheet-bar > i { transition: none; } }
</style>
