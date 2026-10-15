<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from "vue";

// Menu « ⋯ » commun (docs/50 §1) : Échap ferme le seul menu et rend le focus à « ⋯ »,
// un clic ailleurs le ferme, les flèches passent d'une action à l'autre.
export type MoreMenuItem = { label: string; test: string; run: () => void; danger?: boolean };

withDefaults(defineProps<{ items: MoreMenuItem[]; label?: string; testId?: string }>(), {
  label: "Plus d'actions",
  testId: "more",
});

const open = ref(false);
const root = ref<HTMLElement | null>(null);
const toggleButton = ref<HTMLButtonElement | null>(null);

function entries(): HTMLButtonElement[] {
  return [...(root.value?.querySelectorAll<HTMLButtonElement>("[role=menuitem]") ?? [])];
}

async function toggle(): Promise<void> {
  open.value = !open.value;
  if (open.value) {
    await nextTick();
    entries()[0]?.focus();
  }
}

function close(focus = false): void {
  open.value = false;
  if (focus) toggleButton.value?.focus();
}

function choose(item: MoreMenuItem): void {
  close();
  item.run();
}

function onKeydown(event: KeyboardEvent): void {
  if (!open.value) return;
  if (event.key === "Escape") {
    // Le panneau latéral autour, ou l'offre ouverte, ne doivent pas se fermer aussi.
    event.preventDefault();
    event.stopPropagation();
    close(true);
  } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const list = entries();
    const at = list.indexOf(document.activeElement as HTMLButtonElement);
    const next = event.key === "ArrowDown" ? at + 1 : at - 1;
    list[(next + list.length) % list.length]?.focus();
  }
}

function onDocumentClick(event: MouseEvent): void {
  if (open.value && root.value && !root.value.contains(event.target as Node)) close();
}
onMounted(() => document.addEventListener("click", onDocumentClick));
onUnmounted(() => document.removeEventListener("click", onDocumentClick));
</script>

<template>
  <div
    ref="root"
    class="more-menu"
    @keydown="onKeydown"
  >
    <button
      ref="toggleButton"
      type="button"
      class="more-button"
      :aria-label="label"
      aria-haspopup="menu"
      :aria-expanded="open"
      :data-test="testId"
      @click="toggle"
    >
      ⋯
    </button>
    <ul
      v-if="open"
      class="menu"
      role="menu"
    >
      <li
        v-for="item in items"
        :key="item.test"
      >
        <button
          type="button"
          role="menuitem"
          :class="{ danger: item.danger }"
          :data-test="item.test"
          @click="choose(item)"
        >
          {{ item.label }}
        </button>
      </li>
    </ul>
  </div>
</template>
