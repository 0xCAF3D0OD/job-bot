<script setup lang="ts">
import { computed } from "vue";

import type { Training } from "../api/client";
import { languageLabel } from "../newsLabels";
import { FORMATS, SHORT_FORMATS } from "../trainingLabels";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";

// Une formation en ligne, dans la carte de son groupe (maquette Explorer, onglet Formations ; B18, 8e) :
// l'icône du genre, le titre, « éditeur · format · langue », le prix et l'avancement en étiquettes, puis le
// signet à droite. La ligne ouvre le panneau ; une suggestion de l'IA « à vérifier » se garde ou s'écarte.
const props = defineProps<{ training: Training }>();
const emit = defineEmits<{ open: []; interest: []; review: [keep: boolean] }>();

const FUNDING: Record<string, string> = {
  requested: "Financement demandé",
  accepted: "Financement accordé",
  granted: "Financement accordé",
  refused: "Financement refusé",
};

const cert = computed(() => props.training.kind === "certification");
const status = computed(() => props.training.mark?.status ?? null);
const meta = computed(() => {
  const t = props.training;
  const format = SHORT_FORMATS[t.format] ?? t.format;
  return `${t.provider} · ${format.charAt(0).toUpperCase()}${format.slice(1)} · ${languageLabel(t.language)}`;
});
// L'avancement (B19) : le texte libre tel quel, en attendant le compteur de modules.
const progress = computed(() => {
  const mark = props.training.mark;
  if (mark?.status === "in_progress") return mark.progress ? `En cours · ${mark.progress}` : "En cours";
  if (mark?.status === "done") return "Terminée";
  return "";
});
// Le signet (docs/101) : vide, il garde la formation ; plein, elle est gardée ou suivie.
const keepLabel = computed(() =>
  !status.value
    ? `Garder : ${props.training.title}`
    : status.value === "interested"
      ? `Retirer des formations gardées : ${props.training.title}`
      : `Formation suivie : ${props.training.title}`,
);

function onKeep(): void {
  // En cours ou terminée : on ouvre le panneau plutôt que d'effacer le suivi par erreur.
  if (status.value && status.value !== "interested") emit("open");
  else emit("interest");
}
</script>

<template>
  <div
    class="training-row"
    data-test="training"
  >
    <button
      type="button"
      class="training-row-open"
      data-test="training-open"
      @click="emit('open')"
    >
      <span
        :class="['training-row-icon', { cert }]"
        aria-hidden="true"
      ><AppIcon :name="cert ? 'star' : 'book'" /></span>
      <span class="training-row-text">
        <strong>{{ training.title }}</strong>
        <span :title="FORMATS[training.format]">{{ meta }}</span>
        <span class="training-row-tags">
          <span
            :class="['training-tag', training.price === 'free' ? 'free' : 'paid']"
            data-test="training-price"
          >{{ training.price === "free" ? "Gratuit" : "Payant" }}</span>
          <span
            v-if="progress"
            class="training-tag progress"
            data-test="training-progress"
          >{{ progress }}</span>
          <span
            v-if="training.mark?.funding_status"
            class="training-tag"
            data-test="funding-badge"
          >{{ FUNDING[training.mark.funding_status] }}</span>
          <span
            v-if="!training.verified"
            class="training-tag"
            data-test="unverified"
          >À vérifier</span>
        </span>
      </span>
    </button>
    <span
      v-if="!training.verified"
      class="training-row-review"
    >
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
    </span>
    <IconButton
      v-else
      icon="bookmark"
      :label="keepLabel"
      :class="['training-keep', { on: status }]"
      :aria-pressed="Boolean(status)"
      data-test="interest"
      @click="onKeep"
    />
  </div>
</template>
