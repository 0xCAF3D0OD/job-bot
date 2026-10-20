<script setup lang="ts">
import { computed } from "vue";

import type { Training } from "../api/client";
import { highlight, languageLabel } from "../newsLabels";
import { FORMATS, KINDS, PRICES, SHORT_FORMATS, STATUSES } from "../trainingLabels";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";

// Une formation en carte (docs/93), à la manière des offres de Sphere : les étiquettes, le
// titre, trois faits sur leur ligne, et le signet (docs/101). La carte entière ouvre le panneau ; elle ne
// garde que ce qui sert à choisir, la description est dans le panneau. Aérée : docs/93 §1.
const props = defineProps<{ training: Training }>();
const emit = defineEmits<{ open: []; interest: []; review: [keep: boolean] }>();

const FUNDING: Record<string, string> = {
  requested: "Financement demandé",
  granted: "Financement accordé",
  refused: "Financement refusé",
};

const status = computed(() => props.training.mark?.status ?? null);
// Avancement d'une formation en cours ; sinon le format et la langue.
const second = computed(() => {
  const t = props.training;
  if (t.mark?.status === "in_progress" && t.mark.progress) {
    return { icon: "clock" as const, text: t.mark.progress, title: undefined };
  }
  const format = SHORT_FORMATS[t.format] ?? t.format;
  // Format court sur la carte, complet dans l'infobulle (docs/43 n° 22).
  return {
    icon: "globe" as const,
    text: `${format.charAt(0).toUpperCase()}${format.slice(1)} · ${languageLabel(t.language)}`,
    title: FORMATS[t.format],
  };
});
const price = computed(() => {
  const t = props.training;
  const value = PRICES[t.price] ?? t.price;
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}${t.duration ? ` · ${t.duration}` : ""}`;
});
// Le signet (docs/101, à la place du cœur) : vide, il garde la formation (« Intéressé ») ;
// plein, elle est gardée ou suivie.
const heartLabel = computed(() =>
  !status.value ? "Garder" : status.value === "interested" ? "Gardée" : "Formation suivie",
);

function onHeart(): void {
  // En cours ou terminée : on ouvre le panneau plutôt que d'effacer le suivi par erreur.
  if (status.value && status.value !== "interested") emit("open");
  else emit("interest");
}
</script>

<template>
  <article class="training-tile">
    <div class="tile-tags">
      <span class="tile-tag strong">{{ KINDS[training.kind] ?? training.kind }}</span>
      <span
        v-if="status"
        class="tile-tag"
        data-test="training-state"
      >{{ STATUSES[status] }}</span>
      <span
        v-if="training.mark?.funding_status"
        :class="['tile-tag', { warn: training.mark.funding_status === 'refused' }]"
        data-test="funding-badge"
      >{{ FUNDING[training.mark.funding_status] }}</span>
      <span
        v-if="!training.verified"
        class="tile-tag warn"
        data-test="unverified"
      >à vérifier</span>
    </div>
    <h3 class="tile-title">
      <button
        type="button"
        class="tile-open"
        data-test="training-open"
        @click="emit('open')"
      >
        <template
          v-for="(part, index) in highlight(training.title, training.matched)"
          :key="index"
        >
          <mark v-if="part.hit">{{ part.text }}</mark><template v-else>
            {{ part.text }}
          </template>
        </template>
      </button>
    </h3>
    <ul class="tile-facts">
      <li>
        <AppIcon name="building" />
        <span>{{ training.provider }}</span>
      </li>
      <li data-test="training-second">
        <AppIcon :name="second.icon" />
        <span :title="second.title">{{ second.text }}</span>
      </li>
      <li>
        <AppIcon name="tag" />
        <span>{{ price }}</span>
      </li>
    </ul>
    <div class="tile-foot">
      <template v-if="!training.verified">
        <IconButton
          icon="bookmark"
          label="Garder"
          data-test="keep"
          @click="emit('review', true)"
        />
        <IconButton
          icon="trash"
          label="Écarter"
          danger
          data-test="dismiss"
          @click="emit('review', false)"
        />
      </template>
      <IconButton
        v-else
        icon="bookmark"
        :label="heartLabel"
        :class="['tile-heart', { on: status }]"
        :aria-pressed="Boolean(status)"
        data-test="interest"
        @click="onHeart"
      />
    </div>
  </article>
</template>
