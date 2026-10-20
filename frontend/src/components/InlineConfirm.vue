<script setup lang="ts">
import { onMounted, ref } from "vue";

// Une confirmation dans la page (docs/108 §1), à l'endroit du bouton : ce qui va se passer,
// l'action (rouge si elle détruit), et « Garder ». Le focus va sur « Garder » : Entrée ne
// détruit rien par mégarde.
withDefaults(
  defineProps<{ message: string; confirmLabel?: string; cancelLabel?: string; altLabel?: string; danger?: boolean; busy?: boolean }>(),
  {
    confirmLabel: "Supprimer",
    cancelLabel: "Garder",
    altLabel: "",
    danger: true,
    busy: false,
  },
);
// `alt` : une troisième voie, quand il y en a une (« Rédiger sans enregistrer »).
const emit = defineEmits<{ confirm: []; cancel: []; alt: [] }>();
const keep = ref<HTMLButtonElement | null>(null);
onMounted(() => keep.value?.focus({ preventScroll: true }));
</script>

<template>
  <div
    class="inline-confirm"
    role="group"
    :aria-label="message"
    data-test="inline-confirm"
    @keydown.esc="emit('cancel')"
  >
    <p>{{ message }}</p>
    <slot />
    <div class="inline-confirm-actions">
      <button
        type="button"
        :class="danger ? 'secondary small danger' : 'primary small'"
        :disabled="busy"
        data-test="inline-confirm-yes"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </button>
      <button
        v-if="altLabel"
        type="button"
        class="secondary small"
        :disabled="busy"
        data-test="inline-confirm-alt"
        @click="emit('alt')"
      >
        {{ altLabel }}
      </button>
      <button
        ref="keep"
        type="button"
        class="secondary small"
        data-test="inline-confirm-no"
        @click="emit('cancel')"
      >
        {{ cancelLabel }}
      </button>
    </div>
  </div>
</template>
