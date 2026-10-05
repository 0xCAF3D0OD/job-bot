<script setup lang="ts">
import { ref } from "vue";

const model = defineModel<string[]>({ required: true });
defineProps<{ id: string; placeholder?: string }>();

const draft = ref("");

function add(): void {
  for (const part of draft.value.split(",")) {
    const value = part.trim();
    if (value && !model.value.some((v) => v.toLowerCase() === value.toLowerCase())) {
      model.value = [...model.value, value];
    }
  }
  draft.value = "";
}

function remove(value: string): void {
  model.value = model.value.filter((v) => v !== value);
}
</script>

<template>
  <div class="tag-input">
    <ul
      v-if="model.length"
      class="tags"
    >
      <li
        v-for="value in model"
        :key="value"
        class="tag"
      >
        {{ value }}
        <button
          type="button"
          :aria-label="`Retirer ${value}`"
          @click="remove(value)"
        >
          ×
        </button>
      </li>
    </ul>
    <div class="tag-add">
      <input
        :id="id"
        v-model="draft"
        type="text"
        :placeholder="placeholder"
        @keydown.enter.prevent="add"
      >
      <button
        type="button"
        class="secondary small"
        :disabled="!draft.trim()"
        @click="add"
      >
        Ajouter
      </button>
    </div>
  </div>
</template>
