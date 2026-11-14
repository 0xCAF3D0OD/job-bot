<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { daysBefore, formatMonth, plural } from "../../format";
import { isNetworkError } from "../../network";
import AppIcon from "../AppIcon.vue";
import FaceState from "../FaceState.vue";
import LoadingBlocks from "../LoadingBlocks.vue";
import NetworkError from "../NetworkError.vue";

// Bilan › Résultats sur ordinateur (récapitulatif du 11 novembre, PR 33 point 3 ; maquette BilanOrdinateur, onglet
// Résultats) : une seule colonne. Les trois chiffres des 3 derniers mois dans une carte, « Le mois en bref » (le mois
// en cours et le précédent, avec l'objectif ORP), puis « Ce qui bloque » : les réponses, les sites d'où viennent
// les candidatures, celles qui attendent une relance, et l'action « Relancer les n candidatures ». La période, le
// Parcours et la colonne de droite (« Mois par mois », « Ce qui marche », « Entretiens ») sont partis.
type Insights = components["schemas"]["SearchReportOut"];
type MonthFacts = components["schemas"]["MonthFactsOut"];
type Today = components["schemas"]["TodayOut"];

const SOURCES_SHOWN = 4;
// Le texte du serveur garde l'apostrophe droite ; l'écran montre la typographique.
const curly = (text: string) => text.replace(/'/g, "\u2019");
const advice = computed(() =>
  (insights.value?.advice ?? []).map((a) => ({
    kind: a.kind,
    link: a.link ?? null,
    title: curly(a.title),
    text: curly(a.text),
    base: `d\u2019après ${plural(a.base, a.base_unit === "offers" ? "offre" : "candidature", a.base_unit === "offers" ? "offres" : "candidatures")}`,
  })),
);
const insights = ref<Insights | null>(null);
const months = ref<MonthFacts[]>([]);
const today = ref<Today | null>(null);
const error = ref(false);
const offline = ref(false);
const emit = defineEmits<{ ready: [] }>();

async function load(): Promise<void> {
  error.value = false;
  offline.value = false;
  try {
    const [report, meeting, day] = await Promise.all([
      api.GET("/api/insights", { params: { query: { period: "recent" } } }),
      api.GET("/api/orp-meeting").catch(() => null),
      api.GET("/api/today").catch(() => null),
    ]);
    if (!report.data) throw new Error();
    insights.value = report.data;
    // Le mois en cours d'abord.
    months.value = [...(meeting?.data?.preparation?.months ?? [])].sort((a, b) => b.month.localeCompare(a.month));
    today.value = day?.data ?? null;
  } catch (cause) {
    error.value = true;
    offline.value = isNetworkError(cause);
  } finally {
    emit("ready");
  }
}
onMounted(() => void load());

const funnel = computed(() => insights.value?.funnel ?? null);
const figures = computed(() => {
  const f = funnel.value;
  if (!f) return [];
  return [
    { key: "applications", value: f.applications, label: `${f.applications <= 1 ? "candidature" : "candidatures"} en 3 mois` },
    { key: "responses", value: f.responses, label: f.responses <= 1 ? "réponse" : "réponses" },
    { key: "interviews", value: f.interviews, label: f.interviews <= 1 ? "entretien" : "entretiens" },
  ];
});
const monthTitle = (month: string) => formatMonth(month).replace(/^./, (c) => c.toUpperCase());
const monthLines = computed(() =>
  months.value.map((m) => ({
    month: m.month,
    title: monthTitle(m.month),
    count: m.target ? `${m.count} sur ${m.target}` : String(m.count),
    part: m.target ? Math.min(100, Math.round((m.count / m.target) * 100)) : null,
    line: `${plural(m.answered, "réponse", "réponses")} · ${plural(m.interviews, "entretien", "entretiens")}`,
  })),
);
const sources = computed(() =>
  [...(insights.value?.comparisons.find((c) => c.key === "source")?.groups ?? [])]
    .filter((g) => g.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, SOURCES_SHOWN),
);
// Celles qui attendent une relance (les mêmes que dans Aujourd'hui) et la plus ancienne.
const waiting = computed(() => today.value?.to_follow_up ?? 0);
const oldest = computed(() => Math.max(0, ...(today.value?.follow_ups ?? []).map((f) => daysBefore(f.sent_at))));
</script>

<template>
  <!-- Refait à zéro d’après la planche BilanOrdinateur, état Résultats (règle de Kevin du 14.11, 15 h 55) : quatre
       blocs l’un sous l’autre, espacés de 32 ; les états d’erreur, de chargement et « Trop tôt » viennent de main. -->
  <div
    class="res"
    data-test="bilan-results"
  >
    <NetworkError
      v-if="error && offline"
      @retry="load()"
    />
    <p
      v-else-if="error"
      class="notice error"
      role="alert"
    >
      Bilan indisponible pour l’instant.
    </p>
    <LoadingBlocks
      v-else-if="!insights || !funnel"
      :heights="['6rem', '10rem', '16rem']"
    />
    <FaceState
      v-else-if="funnel.applications === 0"
      title="Trop tôt pour conclure"
      illustration="trop-tot"
      data-test="insights-empty"
    >
      <p>Le Bilan se remplit avec tes premières candidatures et réponses.</p>
      <div class="face-state-actions">
        <RouterLink
          to="/candidatures/offres"
          class="button-link primary-link"
        >
          <span class="with-icon"><AppIcon name="briefcase" />Voir les offres</span>
        </RouterLink>
      </div>
    </FaceState>
    <template v-else>
      <!-- Les trois chiffres : carte à filet bleu clair et ombre, remontée de 8. -->
      <ul
        class="res-figures"
        data-test="bilan-figures"
      >
        <li
          v-for="figure in figures"
          :key="figure.key"
          :data-test="`figure-${figure.key}`"
        >
          <strong>{{ figure.value }}</strong>
          <span>{{ figure.label }}</span>
        </li>
      </ul>

      <section
        v-if="monthLines.length"
        class="res-block"
        aria-labelledby="bilan-months-title"
        data-test="bilan-months"
      >
        <div class="res-head bilan-section-head">
          <h2 id="bilan-months-title">
            Le mois en bref
          </h2>
        </div>
        <ul class="res-card">
          <li
            v-for="m in monthLines"
            :key="m.month"
            class="res-month"
            :data-test="`bilan-month-${m.month}`"
          >
            <div class="res-month-top bilan-month-head">
              <span>{{ m.title }}</span><span>{{ m.count }}</span>
            </div>
            <div
              v-if="m.part !== null"
              class="res-bar bilan-month-bar"
              aria-hidden="true"
            >
              <div :style="{ width: `${m.part}%` }" />
            </div>
            <span class="res-month-line bilan-month-line">{{ m.line }}</span>
          </li>
        </ul>
      </section>

      <section
        class="res-block"
        aria-labelledby="bilan-blocks-title"
        data-test="bilan-blocks"
      >
        <div class="res-head bilan-section-head">
          <h2 id="bilan-blocks-title">
            Ce qui bloque
          </h2>
          <span>sur {{ plural(funnel.applications, "candidature", "candidatures") }}</span>
        </div>
        <ul class="res-card">
          <li
            class="res-row"
            data-test="bilan-block-responses"
          >
            <span class="res-what">Réponses en 3 mois</span>
            <strong :class="{ warn: funnel.responses === 0 }">{{ funnel.responses }}</strong>
          </li>
          <li
            v-for="source in sources"
            :key="source.key"
            class="res-row"
            :data-test="`bilan-block-source-${source.key}`"
          >
            <span class="res-what">{{ source.label }}<span>{{ plural(source.total, "candidature", "candidatures") }}</span></span>
            <strong>{{ plural(source.responses, "réponse", "réponses") }}</strong>
          </li>
          <li
            v-if="waiting"
            class="res-row"
            data-test="bilan-block-waiting"
          >
            <span class="res-what">Jamais relancées<span v-if="oldest">{{ waiting === 1 ? "Elle attend" : "La plus ancienne attend" }} depuis {{ plural(oldest, "jour", "jours") }}</span></span>
            <strong class="warn">{{ waiting }}</strong>
          </li>
          <li v-if="waiting">
            <RouterLink
              to="/candidatures/suivi"
              class="res-action"
              data-test="bilan-block-action"
            >
              {{ waiting === 1 ? "Relancer la candidature" : `Relancer les ${waiting} candidatures` }}<AppIcon name="chevron" />
            </RouterLink>
          </li>
        </ul>
      </section>

      <!-- « Ce que jobA1 conseille » (Kevin, 2026-11-14) : sans conseil, le bloc est caché ; la base à droite. -->
      <section
        v-if="advice.length"
        class="res-block"
        aria-labelledby="bilan-advice-title"
        data-test="bilan-advice"
      >
        <div class="res-head bilan-section-head">
          <h2 id="bilan-advice-title">
            Ce que jobA1 conseille
          </h2>
        </div>
        <ul class="res-card">
          <li
            v-for="item in advice"
            :key="item.kind"
            :data-test="`bilan-advice-${item.kind}`"
          >
            <component
              :is="item.link ? RouterLink : 'div'"
              :to="item.link ?? undefined"
              :class="['res-row', { 'res-row-link': item.link }]"
            >
              <span class="res-what">{{ item.title }}<span>{{ item.text }}</span></span>
              <span
                class="res-base"
                data-test="bilan-advice-base"
              >{{ item.base }}</span>
              <span
                v-if="item.link"
                class="res-arrow"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </component>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style>
/* Les valeurs de la planche BilanOrdinateur (état Résultats), une à une : blocs espacés de 32 ; titre 18/700 et
   remarque 14 à 4 du bord, 10 au-dessus de la carte ; cartes blanches de rayon 18, filets #ECE9E1 ; chiffres en
   cases de 20/24, 30/800 ; mois 14/20, barre de 6 (8 au-dessus, 6 au-dessous), ligne 13 ; lignes d'au moins 56
   (12/20, écart 14), texte 15/21, sous-ligne 14 à 2, valeur 15/700, brun pour ce qui attend ; action de 52 ; cercle
   de 36 à trait de 2. */
.res {
  --res-2: 2px; --res-6: 6px; --res-10: 10px; --res-14: 14px; --res-30: 30px; --res-36: 36px; --res-52: 52px;
  --res-56: 56px; --res-lh: 21px; --res-13: 0.8125rem; --res-15: 0.9375rem; --res-18: 1.125rem;
  display: flex; flex-direction: column; gap: var(--space-8);
}
.res-figures { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: calc(-1 * var(--space-2)) 0 0; padding: 0; list-style: none; background: var(--surface); border: 1px solid var(--water); border-radius: var(--radius-card); box-shadow: var(--shadow-band-card); }
.res-figures li { padding: var(--space-5) var(--space-6); }
.res-figures li + li { border-left: 1px solid var(--surface-muted); }
.res-figures strong { display: block; font-size: var(--res-30); font-weight: var(--weight-heavy); font-variant-numeric: tabular-nums; }
.res-figures span { font-size: var(--font-small); color: var(--text-secondary); }
.res-block { display: flex; flex-direction: column; gap: var(--res-10); }
.res .res-head { display: flex; align-items: baseline; justify-content: space-between; margin: 0 var(--space-1); }
.res .res-head h2 { margin: 0; font-size: var(--res-18); font-weight: var(--weight-bold); }
.res .res-head span { font-size: var(--font-small); color: var(--text-secondary); }
.res-card { margin: 0; padding: 0; overflow: hidden; list-style: none; background: var(--surface); border-radius: var(--radius-card); }
.res-card > li + li { border-top: 1px solid var(--surface-muted); }
.res-month { padding: var(--res-14) var(--space-5); }
.res-month-top { display: flex; justify-content: space-between; font-size: var(--res-15); font-weight: var(--weight-bold); }
.res-bar { height: var(--res-6); margin: var(--space-2) 0 var(--res-6); overflow: hidden; border-radius: var(--radius-pill); background: var(--surface-muted); }
.res-bar > div { height: 100%; border-radius: var(--radius-pill); background: var(--primary-graphic); }
.res-month-line { font-size: var(--res-13); color: var(--text-secondary); }
.res-row { display: flex; align-items: center; gap: var(--res-14); box-sizing: border-box; min-height: var(--res-56); padding: var(--space-3) var(--space-5); }
.res-what { flex: 1; min-width: 0; font-size: var(--res-15); line-height: var(--res-lh); }
.res-what > span { display: block; margin-top: var(--res-2); font-size: var(--font-small); color: var(--text-secondary); }
.res-row > strong { flex: none; font-size: var(--res-15); font-weight: var(--weight-bold); }
.res-row > strong.warn { color: var(--peach-text); }
.res-action { display: flex; align-items: center; justify-content: space-between; min-height: var(--res-52); padding: 0 var(--space-5); border-radius: 0; font-size: var(--res-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.res-action:hover { background: var(--primary-soft); }
.res-row-link { border-radius: 0; color: var(--text); text-decoration: none; }
.res-row-link:hover { background: var(--surface-muted); }
.res-base { flex: none; font-size: var(--font-small); color: var(--text-secondary); }
.res-arrow { display: flex; flex: none; align-items: center; justify-content: center; box-sizing: border-box; width: var(--res-36); height: var(--res-36); border: var(--res-2) solid var(--text-secondary); border-radius: var(--radius-pill); color: var(--text-secondary); }
.res-arrow .icon { width: 18px; height: 18px; }
</style>
