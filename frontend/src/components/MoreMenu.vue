<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from "vue";

// Menu « ⋯ » commun (docs/50 §1) : Échap ferme le seul menu et rend le focus à « ⋯ »,
// un clic ailleurs le ferme, les flèches passent d'une action à l'autre.
// docs/74 §5 : une action peut être un lien (page externe « ↗ » ou fichier à télécharger),
// porter un nombre ; les suppressions viennent en dernier, après un filet.
export type MoreMenuItem = {
  label: string;
  test: string;
  run?: () => void;
  href?: string;
  /** Lien vers un fichier : téléchargé, sans nouvel onglet. */
  download?: boolean;
  count?: number;
  disabled?: boolean;
  danger?: boolean;
};

const props = withDefaults(defineProps<{ items: MoreMenuItem[]; label?: string; testId?: string }>(), {
  label: "Plus d'actions",
  testId: "more",
});

const open = ref(false);
const up = ref(false);
const alignLeft = ref(false);
const root = ref<HTMLElement | null>(null);
const menu = ref<HTMLElement | null>(null);
const toggleButton = ref<HTMLButtonElement | null>(null);

function entries(): HTMLButtonElement[] {
  return [...(root.value?.querySelectorAll<HTMLButtonElement>("[role=menuitem]") ?? [])];
}

async function toggle(): Promise<void> {
  open.value = !open.value;
  if (open.value) {
    up.value = false;
    alignLeft.value = false;
    await nextTick();
    place();
    entries()[0]?.focus();
  }
}

// Le menu ne sort jamais de l'écran : vers le haut s'il manque de place dessous, aligné à
// gauche de « ⋯ » s'il déborderait à gauche.
// La marge du bas tient compte d'une barre fixe en bas de l'écran (téléphone).
function place(): void {
  const box = root.value?.getBoundingClientRect();
  const list = menu.value?.getBoundingClientRect();
  if (!box || !list || !list.height || !menu.value) return;
  const bottomGap = parseFloat(getComputedStyle(menu.value).scrollMarginBottom) || 8;
  up.value = box.bottom + list.height + bottomGap > window.innerHeight && box.top - list.height - 8 > 0;
  alignLeft.value = box.right - list.width < 8;
  menu.value.scrollIntoView?.({ block: "nearest" });
}

function close(focus = false): void {
  open.value = false;
  if (focus) toggleButton.value?.focus();
}

function choose(item: MoreMenuItem): void {
  close();
  item.run?.();
}

function separated(index: number, items: MoreMenuItem[]): boolean {
  return Boolean(items[index]?.danger) && index > 0 && !items[index - 1]?.danger;
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
      ref="menu"
      :class="['menu', { up, 'align-left': alignLeft }]"
      role="menu"
    >
      <template
        v-for="(item, index) in props.items"
        :key="item.test"
      >
        <li
          v-if="separated(index, props.items)"
          role="separator"
          class="menu-separator"
        />
        <li role="none">
          <a
            v-if="item.href"
            role="menuitem"
            :href="item.href"
            :class="{ danger: item.danger }"
            :data-test="item.test"
            v-bind="item.download ? { download: '' } : { target: '_blank', rel: 'noopener noreferrer' }"
            @click="choose(item)"
          >{{ item.label }}<span
            v-if="!item.download"
            aria-hidden="true"
          > ↗</span><span
            v-if="!item.download"
            class="visually-hidden"
          > (nouvel onglet)</span></a>
          <button
            v-else
            type="button"
            role="menuitem"
            :class="{ danger: item.danger }"
            :disabled="item.disabled"
            :data-test="item.test"
            @click="choose(item)"
          >
            {{ item.label }}<span
              v-if="item.count"
              class="menu-count"
            > ({{ item.count }})</span>
          </button>
        </li>
      </template>
    </ul>
  </div>
</template>
