<script setup lang="ts">
import { computed, ref, useId } from "vue";

import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import ScoreRing from "./ScoreRing.vue";

// La feuille « Compatibilité » du détail d'une offre sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.1, 3 bis ;
// maquettes OffreCompatibilite et OffreCompatibiliteSombre) : le même composant que Filtres (BottomSheet). En haut,
// le rappel (anneau, verdict, « poste · entreprise ») ; puis deux familles, « Points forts · n » et « À vérifier · n »,
// en cascade (§2.10) : l'icône de 24 px de chaque critère commence sous le titre de sa famille, 16 px avant le texte,
// le libellé au-dessus de la valeur ; la valeur d'un point à vérifier est aussi orange (WCAG 1.4.1). Une famille vide
// n'est pas affichée. Données : un point s'écrit « Critère : valeur » ; sans deux-points, la phrase entière est la
// valeur, sans libellé (question pour Kevin dans la PR).
export interface CompatPoint {
  key: string;
  value: string;
}
// « Comment la note est calculée » (prompt du 10 novembre, PR 18) : les cinq parts du vrai calcul (score-v7),
// l'action qui ferait monter la note, la date et la source.
export type PartKey = "skills" | "experience" | "location" | "languages" | "terms";
export type TipAction = "skills" | "experience" | "languages" | "criteria";
export interface ScorePart {
  key: PartKey;
  points: number;
  max: number;
  text: string;
  check?: boolean;
}
export interface ScoreTip {
  text: string;
  action?: TipAction | null;
}
const PART_LABELS: Record<PartKey, string> = {
  skills: "Compétences demandées",
  experience: "Expérience",
  location: "Lieu et trajet",
  languages: "Langues",
  terms: "Taux et contrat",
};
const TIP_LABELS: Record<TipAction, string> = {
  skills: "Ajouter une compétence",
  experience: "Ajouter une expérience",
  languages: "Indiquer mes langues",
  criteria: "Changer ce que je cherche",
};

const props = defineProps<{
  open: boolean;
  score: number | null;
  provisional?: boolean;
  stale?: boolean;
  verdict: string;
  tone: string;
  subtitle: string;
  strengths: CompatPoint[];
  gaps: CompatPoint[];
  // « Comment la note est calculée » : dépliée sur place, puisqu'on n'ouvre pas une feuille depuis une autre.
  // Les cinq parts quand la note les a (score-v7) ; sinon, pour une note plus ancienne, l'explication d'avant
  // (le « pourquoi », le niveau) : aucun point n'est inventé.
  how: string[];
  parts?: ScorePart[];
  tip?: ScoreTip | null;
  scoredAt?: string | null;
}>();
const emit = defineEmits<{ close: []; tip: [action: TipAction] }>();

const strongId = useId();
const gapId = useId();
const howId = useId();
const howOpen = ref(false);
const parts = computed(() => props.parts ?? []);
// Barre : verte si pleine, orange si la part dépend d'un point à vérifier, bleue sinon. Le chiffre est
// toujours écrit à côté (WCAG 1.4.1).
const barTone = (part: ScorePart): string => (part.points >= part.max ? "full" : part.check ? "check" : "partial");
const width = (part: ScorePart): string => `${Math.round((100 * Math.min(part.points, part.max)) / part.max)}%`;
const source = computed(() => (props.provisional ? "l’extrait de l’alerte" : "l’annonce complète"));
const foot = computed(() =>
  props.scoredAt ? `Calculée ${dateInSentence(props.scoredAt)} sur ${source.value}.` : "",
);
const hasHow = computed(() => parts.value.length > 0 || props.how.length > 0);
const families = computed(() =>
  [
    { id: strongId, title: "Points forts", tone: "ok", icon: "check-circle" as const, points: props.strengths },
    { id: gapId, title: "À vérifier", tone: "gap", icon: "alert-circle" as const, points: props.gaps },
  ].filter((family) => family.points.length),
);
</script>

<template>
  <BottomSheet
    :open="open"
    title="Compatibilité"
    data-test="compat-sheet"
    @close="$emit('close')"
  >
    <div class="compat-sum">
      <ScoreRing
        :score="score"
        :provisional="provisional"
        :stale="stale"
        large
        bare
      />
      <div class="compat-sum-text">
        <b :class="['compat-verdict', `is-${tone}`]">{{ verdict }}</b>
        <span class="compat-sum-sub">{{ subtitle }}</span>
      </div>
    </div>
    <section
      v-for="family in families"
      :key="family.id"
      :class="['compat-family', 'grille-fam', family.tone]"
      :aria-labelledby="family.id"
      :data-test="`compat-${family.tone}`"
    >
      <h3
        :id="family.id"
        class="compat-family-title grille-fh"
      >
        <b>{{ family.title }} · {{ family.points.length }}</b>
      </h3>
      <ul class="compat-points">
        <li
          v-for="point in family.points"
          :key="point.key + point.value"
          class="compat-point grille-kd"
        >
          <AppIcon :name="family.icon" />
          <div class="compat-point-text">
            <div
              v-if="point.key"
              class="compat-key"
            >
              {{ point.key }}
            </div>
            <div class="compat-value">
              {{ point.value }}
            </div>
          </div>
        </li>
      </ul>
    </section>
    <template v-if="hasHow">
      <button
        type="button"
        class="compat-how"
        :aria-expanded="howOpen"
        :aria-controls="howId"
        data-test="compat-how"
        @click="howOpen = !howOpen"
      >
        Comment la note est calculée
        <AppIcon :name="howOpen ? 'chevron-up' : 'chevron-down'" />
      </button>
      <div
        v-show="howOpen"
        :id="howId"
        class="compat-how-panel"
      >
        <template v-if="parts.length">
          <p class="compat-calc-intro">
            jobA1 compare {{ source }} à ton profil. Chaque partie vaut un nombre de points, le total fait la note sur 100.
          </p>
          <ul
            class="compat-parts"
            data-test="compat-parts"
          >
            <li
              v-for="part in parts"
              :key="part.key"
              :class="['compat-part', `is-${barTone(part)}`]"
              :data-test="`compat-part-${part.key}`"
            >
              <div class="compat-part-head">
                <b>{{ PART_LABELS[part.key] }}</b>
                <span class="compat-part-points"><b>{{ part.points }}</b><span> / {{ part.max }}</span></span>
              </div>
              <div
                class="compat-bar"
                role="img"
                :aria-label="`${part.points} points sur ${part.max}`"
              >
                <span :style="{ width: width(part) }" />
              </div>
              <p
                v-if="part.text"
                class="compat-part-text"
              >
                {{ part.text }}
              </p>
            </li>
          </ul>
          <div
            v-if="tip?.text"
            class="compat-tip"
            data-test="compat-tip"
          >
            <b>Pour faire monter la note</b>
            <p>{{ tip.text }}</p>
            <button
              v-if="tip.action"
              type="button"
              class="compat-tip-action"
              data-test="compat-tip-action"
              @click="emit('tip', tip.action)"
            >
              {{ TIP_LABELS[tip.action] }}
            </button>
          </div>
        </template>
        <template v-else>
          <p
            v-for="line in how"
            :key="line"
          >
            {{ line }}
          </p>
          <p
            class="compat-calc-old"
            data-test="compat-calc-old"
          >
            Le détail par partie arrive avec la prochaine note de cette offre.
          </p>
        </template>
        <p
          class="compat-calc-foot"
          data-test="compat-calc-foot"
        >
          {{ foot }} jobA1 ne lit pas d’informations personnelles comme l’âge ou la nationalité.
        </p>
      </div>
    </template>
  </BottomSheet>
</template>

<style>
/* Valeurs du HTML d'OffreCompatibilite : rappel 56 + 16, 20 px dessous et trait ; familles à 20 px, titre 13/16
   en capitales ; critères 12 px au-dessus et en dessous, trait dessous, icône 24 à 8 px du haut ; libellé 13/16,
   valeur 15/20 700 ; lien de bas de 56 px. */
.compat-sum { --compat-sum-gap: 20px; --compat-ring: 56px; display: flex; align-items: center; gap: var(--space-4); padding-bottom: var(--compat-sum-gap); border-bottom: 1px solid var(--line-soft); }
.compat-sum .score-ring.large { flex: none; width: var(--compat-ring); height: var(--compat-ring); }
.compat-sum-text { min-width: 0; }
.compat-verdict { display: block; font-size: var(--font-title); line-height: var(--space-6); }
.compat-verdict.is-very-close, .compat-verdict.is-close { color: var(--success); }
.compat-verdict.is-dig { color: var(--score-dig); }
.compat-verdict.is-far, .compat-verdict.is-none { color: var(--text-secondary); }
.compat-sum-sub { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.compat-family { padding-top: var(--space-5); }
.compat-family-title { margin: 0 0 var(--space-1); font-size: var(--label-caps); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.compat-family.gap .compat-family-title { color: var(--peach-text); }
.compat-points { margin: 0; padding: 0; list-style: none; }
.compat-point { display: flex; align-items: flex-start; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--line-soft); }
.compat-point > .icon { flex: none; width: var(--space-6); height: var(--space-6); margin-top: var(--space-2); color: var(--success); }
.compat-family.gap .compat-point > .icon, .compat-family.gap .compat-value { color: var(--peach-text); }
.compat-point-text { min-width: 0; }
.compat-key { font-size: var(--label-caps); line-height: var(--space-4); color: var(--text-secondary); }
.compat-value { margin-top: var(--space-1); font-size: var(--font-label); line-height: var(--space-5); font-weight: var(--weight-bold); overflow-wrap: anywhere; }
.compat-key:empty + .compat-value { margin-top: 0; }
.compat-how { --compat-how-h: 56px; display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); width: 100%; min-height: var(--compat-how-h); margin-top: var(--space-2); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer; }
.compat-how > .icon { flex: none; width: var(--space-6); height: var(--space-6); }
.compat-how-panel p { margin: 0 0 var(--space-2); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
/* Le calcul (HTML d'OffreCompatibilite, état calc) : intro 14/20 ; une part = 14 px au-dessus et dessous (→ 16 sur
   la grille), trait --line-soft ; titre 15/20, points 15/800 et « / 40 » 500 gris ; barre 6 px à 8 px, rayon 3 ;
   phrase 14/20 à 8 px ; encadré --primary-soft 14 × 16 (→ 16), rayon 14 (→ carte), action de 44 px ; pied 13/18. */
.compat-how-panel { --calc-bar: 6px; --calc-15: 15px; --calc-pts: 800; --calc-unit: 500; }
.compat-how-panel .compat-calc-intro { margin: 0; color: var(--text-tertiary); }
.compat-parts { margin: var(--space-2) 0 0; padding: 0; list-style: none; }
.compat-part { padding: var(--space-4) 0; border-bottom: 1px solid var(--line-soft); }
.compat-part-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); font-size: var(--calc-15); line-height: var(--space-5); }
.compat-part-points { white-space: nowrap; }
.compat-part-points > b { font-weight: var(--calc-pts); }
.compat-part-points > span { font-weight: var(--calc-unit); color: var(--text-secondary); }
.compat-bar { height: var(--calc-bar); margin-top: var(--space-2); border-radius: var(--radius-pill); background: var(--line); overflow: hidden; }
.compat-bar > span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--primary-graphic); }
.compat-part.is-full .compat-bar > span { background: var(--success); }
.compat-part.is-check .compat-bar > span { background: var(--peach-text); }
.compat-how-panel .compat-part-text { margin: var(--space-2) 0 0; color: var(--text-tertiary); }
.compat-tip { margin-top: var(--space-4); padding: var(--space-4); border-radius: var(--radius-card); background: var(--primary-soft); }
.compat-tip > b { display: block; font-size: var(--calc-15); line-height: var(--space-5); color: var(--text); }
.compat-how-panel .compat-tip > p { margin: var(--space-1) 0 0; color: var(--text-lead); }
.compat-tip-action { display: inline-flex; align-items: center; min-height: var(--target-min); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--calc-15); font-weight: var(--weight-bold); cursor: pointer; }
.compat-how-panel .compat-calc-foot { margin: var(--space-4) 0 0; font-size: var(--label-caps); line-height: var(--space-5); color: var(--text-secondary); }
</style>
