<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";

// L'avancement par modules (B19, maquette Explorer › Formations › Suivies ; décision de Kevin du
// 2026-11-04) : « Module 6 sur 12 · 50 % », la barre, puis « Module terminé » avec − et +. L'écran change
// tout de suite ; seule la dernière valeur part au serveur, 500 ms après le dernier appui. Au dernier
// module, « Marquer comme terminée » est proposé, sans changer le statut tout seul.
const SAVE_DELAY_MS = 500;

const props = defineProps<{ title: string; total: number; done: number }>();
const emit = defineEmits<{ save: [done: number]; finish: [done: number] }>();

const count = ref(props.done);
// La nouvelle valeur, annoncée seulement après un appui (pas au chargement de la page).
const announced = ref("");
let timer: ReturnType<typeof setTimeout> | undefined;

// La valeur du serveur ne remplace l'écran que si rien n'attend d'être envoyé.
watch(
  () => props.done,
  (value) => {
    if (timer === undefined) count.value = value;
  },
);

const label = computed(() => `Module ${count.value} sur ${props.total}`);
const percent = computed(() => Math.round((count.value / props.total) * 100));

function flush(): void {
  if (timer === undefined) return;
  clearTimeout(timer);
  timer = undefined;
  if (count.value !== props.done) emit("save", count.value);
}

function step(delta: number): void {
  const next = Math.min(props.total, Math.max(0, count.value + delta));
  if (next === count.value) return;
  count.value = next;
  announced.value = label.value;
  clearTimeout(timer);
  timer = setTimeout(flush, SAVE_DELAY_MS);
}

// « Marquer comme terminée » envoie aussi le compte : un seul envoi, pas deux.
function finish(): void {
  clearTimeout(timer);
  timer = undefined;
  emit("finish", count.value);
}

// La page qui se ferme envoie ce qui attendait encore.
onUnmounted(flush);
</script>

<template>
  <div
    class="training-modules"
    data-test="training-modules"
  >
    <div class="training-modules-line">
      <strong>{{ label }}</strong><span>{{ percent }} %</span>
    </div>
    <div
      class="training-modules-bar"
      role="progressbar"
      :aria-label="`Avancement : ${title}`"
      aria-valuemin="0"
      :aria-valuemax="total"
      :aria-valuenow="count"
      :aria-valuetext="label"
      data-test="modules-bar"
    >
      <span :style="{ width: `${percent}%` }" />
    </div>
    <div class="training-modules-step">
      <span>Module terminé</span>
      <span class="training-modules-buttons">
        <button
          type="button"
          class="training-modules-less"
          aria-label="Un module de moins"
          :disabled="count === 0"
          data-test="module-less"
          @click="step(-1)"
        >
          −
        </button>
        <span
          class="training-modules-count"
          aria-hidden="true"
          data-test="module-count"
        >{{ count }}</span>
        <button
          type="button"
          class="training-modules-more"
          aria-label="Un module de plus"
          :disabled="count === total"
          data-test="module-more"
          @click="step(1)"
        >
          +
        </button>
      </span>
    </div>
    <span
      class="visually-hidden"
      role="status"
      data-test="modules-status"
    >{{ announced }}</span>
    <button
      v-if="count === total"
      type="button"
      class="link training-modules-finish"
      data-test="module-finish"
      @click="finish"
    >
      Marquer comme terminée
    </button>
  </div>
</template>
