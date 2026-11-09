<script setup lang="ts">
import { computed } from "vue";

import { firstTime } from "../composables/useIntro";
import { orpPace } from "../format";
import FaceTile from "./FaceTile.vue";

// Le mois ORP (docs/123 §2, Q), dans Aujourd'hui et le Bilan : la tuile du visage à droite du
// titre, le compte en grand, une barre en segments (un par candidature de l'objectif ; au-delà
// de 15, une barre continue) et une phrase dont le mot porte la couleur de l'humeur.
// `compact` (docs/123 §2, S et U) : tout sur une ligne, la tuile, « Mois ORP · 6 / 10 », les
// segments et le mot.
// `noFace` (1.6.51) : sans la tuile du visage, quand le mois doit prendre toute la place
// (« Mois ORP. » d'Aujourd'hui).
// `band` (maquette du 8 novembre, Aujourd'hui sur ordinateur) : dans la carte à cheval sur la bande, « Mois ORP ·
// novembre » et « 4 sur 13 » sur une ligne, une barre continue, puis ce qui reste et le mot du rythme. Décoratif :
// la carte entière porte la phrase lue.
const props = defineProps<{
  title: string;
  count: number;
  target: number | null;
  month: string;
  sub?: string;
  compact?: boolean;
  noFace?: boolean;
  band?: boolean;
  /** `band` : la phrase sous la barre, à la place de celle du rythme (le Bilan y met l'échéance). */
  line?: string;
  /** L'échéance ORP du mois (§11), pour « Encore n d’ici le 5 décembre ». */
  due?: string | null;
}>();

const SEGMENTS_MAX = 15;
const pace = computed(() => orpPace(props.count, props.target, props.month, new Date(), props.due));
const segments = computed(() => (props.target && props.target <= SEGMENTS_MAX ? props.target : 0));
const share = computed(() => (props.target ? Math.min(100, Math.round((props.count / props.target) * 100)) : 0));
const bandLine = computed(() => {
  if (props.line) return props.line;
  const p = pace.value;
  if (!p) return "";
  return `${p.line.replace(/\.$/, "")} · ${p.word.replace(/\.$/, "").toLowerCase()}`;
});
// Le clin d'œil, une fois par visite, quand l'objectif est atteint.
const wink = pace.value?.state === "reached" && firstTime("orp-wink");
</script>

<template>
  <div
    v-if="band"
    class="orp-month-band"
    data-test="orp-month-band"
  >
    <div class="orp-month-band-head">
      <strong>{{ title }}</strong>
      <strong data-test="month-count">{{ target ? `${count} sur ${target}` : count }}</strong>
    </div>
    <div
      v-if="target"
      class="orp-month-band-bar"
      aria-hidden="true"
    >
      <span :style="{ width: `${share}%` }" />
    </div>
    <span
      v-if="bandLine"
      class="orp-month-band-line"
      data-test="month-left"
    >{{ bandLine }}</span>
  </div>
  <div
    v-else-if="compact"
    class="orp-month compact"
  >
    <FaceTile
      v-if="pace && !noFace"
      :mood="pace.mood"
      :act="pace.state === 'behind'"
      small
      data-test="orp-face"
    />
    <h2 data-test="month-count">
      {{ title }} · {{ count }}{{ target ? ` / ${target}` : "" }}
    </h2>
    <div
      v-if="target"
      :class="['orp-month-bar', { continuous: !segments }]"
      role="progressbar"
      :aria-valuenow="count"
      aria-valuemin="0"
      :aria-valuemax="target"
      aria-label="Objectif ORP du mois"
    >
      <template v-if="segments">
        <span
          v-for="index in segments"
          :key="index"
          :class="['segment', { done: index <= count }]"
        />
      </template>
      <span
        v-else
        class="fill"
        :style="{ width: `${share}%` }"
      />
    </div>
    <strong
      v-if="pace"
      :class="['orp-month-word', pace.state]"
      :title="pace.line"
      data-test="month-left"
    >{{ pace.word.replace(".", "") }}<span class="visually-hidden"> : {{ pace.line }}</span></strong>
  </div>
  <div
    v-else
    class="orp-month"
  >
    <header class="orp-month-head">
      <div>
        <h2>{{ title }}</h2>
        <span
          v-if="sub"
          class="muted"
        >{{ sub }}</span>
      </div>
      <FaceTile
        v-if="pace"
        :mood="pace.mood"
        :act="pace.state === 'behind'"
        :wink="wink"
        data-test="orp-face"
      />
    </header>
    <p
      class="orp-month-count"
      data-test="month-count"
    >
      <strong>{{ count }}</strong>
      <span>{{ target ? ` / ${target} candidatures` : ` ${count === 1 ? "candidature" : "candidatures"}` }}</span>
    </p>
    <div
      v-if="target"
      :class="['orp-month-bar', { continuous: !segments }]"
      role="progressbar"
      :aria-valuenow="count"
      aria-valuemin="0"
      :aria-valuemax="target"
      aria-label="Objectif ORP du mois"
    >
      <template v-if="segments">
        <span
          v-for="index in segments"
          :key="index"
          :class="['segment', { done: index <= count }]"
        />
      </template>
      <span
        v-else
        class="fill"
        :style="{ width: `${share}%` }"
      />
    </div>
    <p
      v-if="pace"
      class="orp-month-line"
      data-test="month-left"
    >
      <strong :class="pace.state">{{ pace.word }}</strong> {{ pace.line }}
    </p>
  </div>
</template>
