<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId } from "vue";

import AppIcon from "./AppIcon.vue";

// Le choix d’une valeur sur ordinateur (LISEZMOI §56 du 17.11, planches ReglagesOrdinateur et menu du compte) : la
// valeur actuelle en gris et un chevron ›, un bouton aria-haspopup="menu". Il ouvre un menu (même dessin que le menu
// « ⋯ ») dont chaque choix est un menuitemradio, coché d’un ✓. Choisir ferme le menu ; Échap le ferme et rend le focus
// au bouton ; les flèches, Début et Fin parcourent les choix ; un clic dehors ou Tab le ferment.
export type MenuChoice = { value: string; label: string; test?: string };

const props = defineProps<{ label: string; choices: MenuChoice[]; modelValue: string; testId?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const id = useId();
const open = ref(false);
const up = ref(false);
const root = ref<HTMLElement | null>(null);
const button = ref<HTMLButtonElement | null>(null);
const current = computed(() => props.choices.find((choice) => choice.value === props.modelValue)?.label ?? "");

function entries(): HTMLElement[] {
  return [...(root.value?.querySelectorAll<HTMLElement>("[role=menuitemradio]") ?? [])];
}

async function toggle(): Promise<void> {
  open.value = !open.value;
  if (!open.value) return;
  up.value = false;
  await nextTick();
  const box = root.value?.getBoundingClientRect();
  const list = root.value?.querySelector(".menu")?.getBoundingClientRect();
  if (box && list) up.value = box.bottom + list.height + 8 > window.innerHeight && box.top - list.height - 8 > 0;
  (entries().find((entry) => entry.getAttribute("aria-checked") === "true") ?? entries()[0])?.focus();
}

function close(focus = false): void {
  open.value = false;
  if (focus) button.value?.focus();
}

function choose(value: string): void {
  if (value !== props.modelValue) emit("update:modelValue", value);
  close(true);
}

function onKeydown(event: KeyboardEvent): void {
  if (!open.value) return;
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    close(true);
  } else if (event.key === "Tab") {
    close();
  } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
    event.preventDefault();
    const list = entries();
    const at = list.indexOf(document.activeElement as HTMLElement);
    const next =
      event.key === "Home" ? 0 : event.key === "End" ? list.length - 1 : event.key === "ArrowDown" ? at + 1 : at - 1;
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
    class="more-menu choice-menu"
    @keydown="onKeydown"
  >
    <button
      :id="id"
      ref="button"
      type="button"
      class="choice-menu-button"
      aria-haspopup="menu"
      :aria-expanded="open"
      :aria-label="`${label} : ${current}`"
      :data-test="testId"
      @click="toggle"
    >
      {{ current }}<AppIcon name="chevron" />
    </button>
    <ul
      v-if="open"
      :class="['menu', { up }]"
      role="menu"
      :aria-labelledby="id"
    >
      <li
        v-for="choice in choices"
        :key="choice.value"
        role="none"
      >
        <button
          type="button"
          role="menuitemradio"
          :aria-checked="choice.value === modelValue"
          :data-test="choice.test ?? `choice-${choice.value}`"
          @click="choose(choice.value)"
        >
          <span class="choice-menu-label">{{ choice.label }}</span><AppIcon
            v-if="choice.value === modelValue"
            name="done"
          />
        </button>
      </li>
    </ul>
  </div>
</template>

<style>
/* La valeur 15 px en gris, le chevron de 18 px, une cible de 44 px (planche ReglagesOrdinateur). */
.choice-menu { --cm-value: 15px; --cm-chevron: 18px; }
.choice-menu-button { display: inline-flex; align-items: center; gap: var(--space-1); min-height: 44px; padding: 0 var(--space-1); border: 0; background: transparent; font: inherit; font-size: var(--cm-value); color: var(--text-secondary); cursor: pointer; }
.choice-menu-button .icon { width: var(--cm-chevron); height: var(--cm-chevron); color: var(--text-secondary); }
.choice-menu .menu { top: calc(100% + var(--space-1)); min-width: 12rem; }
.choice-menu .menu.up { top: auto; bottom: calc(100% + var(--space-1)); }
.choice-menu .menu button { min-height: 44px; }
.choice-menu .menu button[aria-checked="true"] { color: var(--text); font-weight: var(--weight-bold); }
.choice-menu-label { flex: 1; }
.choice-menu .menu .icon { color: var(--primary-graphic); }
</style>
