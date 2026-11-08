<script setup lang="ts">
// Les pastilles de suggestions au-dessus du Composer (maquette du 8 novembre, docs/143 ; Préparer, Assistant) :
// un clic remplit le Composer, sans envoyer.
defineProps<{ items: string[]; label?: string }>();
const emit = defineEmits<{ pick: [text: string] }>();
</script>

<template>
  <ul
    class="suggestion-chips"
    :aria-label="label ?? 'Suggestions'"
    data-test="suggestion-chips"
  >
    <li
      v-for="item in items"
      :key="item"
    >
      <button
        type="button"
        class="suggestion-chip"
        :data-test="`suggestion-${item}`"
        @click="emit('pick', item)"
      >
        {{ item }}
      </button>
    </li>
  </ul>
</template>
