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
const props = defineProps<{ title: string; count: number; target: number | null; month: string; sub?: string; compact?: boolean }>();

const SEGMENTS_MAX = 15;
const pace = computed(() => orpPace(props.count, props.target, props.month));
const segments = computed(() => (props.target && props.target <= SEGMENTS_MAX ? props.target : 0));
const share = computed(() => (props.target ? Math.min(100, Math.round((props.count / props.target) * 100)) : 0));
// Le clin d'œil, une fois par visite, quand l'objectif est atteint.
const wink = pace.value?.state === "reached" && firstTime("orp-wink");
</script>

<template>
  <div
    v-if="compact"
    class="orp-month compact"
  >
    <FaceTile
      v-if="pace"
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
