<script setup lang="ts">
import type { Training } from "../api/client";
import { highlight, languageLabel } from "../newsLabels";
import { FORMATS, KINDS, LEVELS, PRICES, STATUSES } from "../trainingLabels";

// Contenu d'une formation (docs/16 §5) : la carte du catalogue sur ordinateur, la fiche en
// plein écran sur téléphone (docs/34 §2).
export type TrainingStatus = "interested" | "in_progress" | "done";
export type MarkExtra = { progress?: string | null; done_at?: string | null; certified?: boolean | null };
type Status = TrainingStatus;

defineProps<{ training: Training }>();
const emit = defineEmits<{ mark: [status: Status | null, extra?: MarkExtra]; review: [keep: boolean] }>();

const inputValue = (event: Event): string => (event.target as HTMLInputElement).value;
</script>

<template>
  <div class="training-head">
    <span class="news-meta">{{ KINDS[training.kind] }} · {{ training.provider }}</span>
    <span
      v-if="!training.verified"
      class="badge warn"
      data-test="unverified"
    >à vérifier</span>
  </div>
  <a
    class="training-title"
    :href="training.url"
    target="_blank"
    rel="noopener noreferrer"
  ><template
    v-for="(part, index) in highlight(training.title, training.matched)"
    :key="index"
  ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></a>
  <p class="training-facts">
    {{ FORMATS[training.format] }} · {{ languageLabel(training.language) }} · {{ PRICES[training.price] }}
    <template v-if="training.level">
      · {{ LEVELS[training.level] }}
    </template>
    <template v-if="training.duration">
      · {{ training.duration }}
    </template>
  </p>
  <p
    v-if="training.description"
    class="training-text"
  >
    {{ training.description }}
  </p>
  <p
    v-if="training.prep"
    class="training-text"
  >
    <strong>Préparation conseillée :</strong> {{ training.prep }}
  </p>
  <p
    v-if="training.price === 'paid'"
    class="hint"
  >
    Financement possible seulement avec l'accord préalable de ton conseiller ORP.
  </p>
  <div
    v-if="!training.verified"
    class="training-actions"
  >
    <button
      type="button"
      class="secondary small"
      data-test="keep"
      @click="emit('review', true)"
    >
      Garder
    </button>
    <button
      type="button"
      class="link danger"
      data-test="dismiss"
      @click="emit('review', false)"
    >
      Écarter
    </button>
  </div>
  <div class="training-actions">
    <div
      class="segmented"
      role="radiogroup"
      aria-label="Suivi"
    >
      <button
        v-for="(label, key) in STATUSES"
        :key="key"
        type="button"
        role="radio"
        :aria-checked="training.mark?.status === key"
        :data-test="`mark-${key}`"
        @click="emit('mark', training.mark?.status === key ? null : (key as Status))"
      >
        {{ label }}
      </button>
    </div>
  </div>
  <label
    v-if="training.mark?.status === 'in_progress'"
    class="training-field"
  >Progression
    <input
      type="text"
      maxlength="80"
      placeholder="module 4/12"
      :value="training.mark.progress ?? ''"
      data-test="progress"
      @change="emit('mark', 'in_progress', { progress: inputValue($event) })"
    >
  </label>
  <div
    v-if="training.mark?.status === 'done'"
    class="training-field"
  >
    <label>Terminée le
      <input
        type="date"
        :value="training.mark.done_at ?? ''"
        @change="emit('mark', 'done', { done_at: inputValue($event) || null })"
      >
    </label>
    <label class="check">
      <input
        type="checkbox"
        :checked="training.mark.certified ?? false"
        data-test="certified"
        @change="emit('mark', 'done', { certified: !(training.mark.certified ?? false) })"
      > certificat obtenu
    </label>
  </div>
</template>
