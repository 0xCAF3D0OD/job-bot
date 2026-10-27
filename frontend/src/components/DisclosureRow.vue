<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Ligne dépliable (docs/32 §2.1), au style des filtres des offres : le titre, un résumé en
// gris, un chevron qui tourne ; le contenu glisse, souligné d'un trait vertical. Dans un
// même groupe, une seule ligne ouverte à la fois. En option (1.6.61) : une icône dans une pastille
// devant le titre, et une phrase en gris sous le titre (l'enseignement, visible replié).
const props = withDefaults(
  defineProps<{ title: string; value?: string; description?: string; icon?: IconName; group?: string; startOpen?: boolean }>(),
  {
    value: "",
    description: "",
    icon: undefined,
    group: "",
    startOpen: false,
  },
);
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
      <span
        v-if="icon"
        class="disclosure-icon"
        aria-hidden="true"
      ><AppIcon :name="icon" /></span>
      <span
        v-if="description"
        class="disclosure-text"
      >
        <span class="disclosure-title">{{ title }}</span>
        <span
          class="disclosure-description"
          data-test="disclosure-description"
        >{{ description }}</span>
      </span>
      <span
        v-else
        class="disclosure-title"
      >{{ title }}</span>
      <span
        v-if="value"
        class="disclosure-value"
      >{{ value }}</span>
      <span
        class="disclosure-chevron"
        aria-hidden="true"
      ><AppIcon name="chevron" /></span>
    </button>
    <!-- Une action sur le repliable ouvert (« Masquer ») : sur la ligne du titre, pas sur une
         ligne à elle (docs/119). -->
    <div
      v-if="$slots.actions"
      v-show="open"
      class="disclosure-actions"
    >
      <slot name="actions" />
    </div>
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
