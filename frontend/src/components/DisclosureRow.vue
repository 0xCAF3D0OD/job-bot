<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";

// Ligne dépliable (docs/32 §2.1), au style des filtres des offres : le titre, un résumé en
// gris, un chevron qui tourne ; le contenu glisse, souligné d'un trait vertical. Dans un
// même groupe, une seule ligne ouverte à la fois.
const props = withDefaults(defineProps<{ title: string; value?: string; group?: string; startOpen?: boolean }>(), {
  value: "",
  group: "",
  startOpen: false,
});
const emit = defineEmits<{ toggle: [open: boolean] }>();

const id = `disclosure-${Math.random().toString(36).slice(2, 8)}`;
const local = ref(props.startOpen);
const open = computed(() => (props.group ? openInGroup[props.group] === id : local.value));

function toggle(): void {
  const next = !open.value;
  if (props.group) openInGroup[props.group] = next ? id : null;
  else local.value = next;
}

// Le contenu reste monté (comme un <details>) : replié, il est rogné et inerte.
watch(open, (value) => emit("toggle", value));
if (props.group && props.startOpen) openInGroup[props.group] = id;
</script>

<script lang="ts">
const openInGroup = reactive<Record<string, string | null>>({});
</script>

<template>
  <section :class="['disclosure', { open }]">
    <button
      type="button"
      class="disclosure-row"
      :aria-expanded="open"
      :aria-controls="id"
      @click="toggle"
    >
      <span class="disclosure-title">{{ title }}</span>
      <span
        v-if="value"
        class="disclosure-value"
      >{{ value }}</span>
      <span
        class="disclosure-chevron"
        aria-hidden="true"
      ><AppIcon name="chevron" /></span>
    </button>
    <div
      :id="id"
      class="disclosure-panel"
      :inert="!open"
    >
      <div class="disclosure-clip">
        <div class="disclosure-body">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>
