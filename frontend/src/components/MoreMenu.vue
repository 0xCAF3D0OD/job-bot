<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId } from "vue";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Menu « ⋯ » commun (docs/50 §1) : Échap ferme le seul menu et rend le focus à « ⋯ »,
// un clic ailleurs le ferme, les flèches passent d'une action à l'autre.
// docs/74 §5 : une action peut être un lien (page externe « ↗ » ou fichier à télécharger),
// porter un nombre ; les suppressions viennent en dernier, après un filet.
// Planche « tête de carte, Copier et ⋯ » : nommé « Plus d'actions », toujours le dernier élément à droite ;
// pas de rouge dans le menu (une suppression confirme sur place ou propose « Annuler » 6 s).
// docs/101 : chaque action a son icône devant le nom ; sans icône donnée, un lien externe prend
// « ouvrir ailleurs », un fichier « télécharger », une suppression la corbeille.
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
  icon?: IconName;
};

function iconOf(item: MoreMenuItem): IconName | null {
  if (item.icon) return item.icon;
  if (item.href) return item.download ? "download" : "external";
  return item.danger ? "trash" : null;
}

// `inline` : faux quand une autre action est déjà visible à côté (une seule visible par partie).
// `trigger` : un bouton secondaire à libellé (« + Ajouter », 1.6.47) au lieu des trois points ; le menu
// s'ouvre de la même façon. Polaris : les actions d'une page dans son en-tête, regroupées.
const props = withDefaults(
  defineProps<{
    items: MoreMenuItem[];
    label?: string;
    testId?: string;
    inline?: boolean;
    trigger?: string;
    triggerIcon?: IconName;
  }>(),
  { label: "Plus d'actions", testId: "more", inline: true, trigger: undefined, triggerIcon: undefined },
);

// Une seule action ordinaire : pas de menu, l'action directement (docs/76 §3).
const direct = computed(() => {
  const [only] = props.items;
  return props.inline && props.items.length === 1 && only && !only.danger ? only : null;
});
const toggleId = useId();
const open = ref(false);
const up = ref(false);
const alignLeft = ref(false);
const root = ref<HTMLElement | null>(null);
const menu = ref<HTMLElement | null>(null);
const toggleButton = ref<HTMLButtonElement | null>(null);

// Les actions qu'on peut atteindre au clavier (pas celles indisponibles).
function entries(): HTMLElement[] {
  return [...(root.value?.querySelectorAll<HTMLElement>("[role=menuitem]:not(:disabled)") ?? [])];
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
  } else if (event.key === "Tab") {
    // Tab quitte le menu : il se ferme, le focus suit son cours.
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
  <a
    v-if="direct?.href"
    class="link more-direct"
    :href="direct.href"
    :data-test="direct.test"
    v-bind="direct.download ? { download: '' } : { target: '_blank', rel: 'noopener noreferrer' }"
  ><span class="with-icon">{{ direct.label }}<AppIcon :name="direct.download ? 'download' : 'external'" /></span><span
    v-if="!direct.download"
    class="visually-hidden"
  > (nouvel onglet)</span></a>
  <button
    v-else-if="direct"
    type="button"
    class="link more-direct"
    :disabled="direct.disabled"
    :data-test="direct.test"
    @click="direct.run?.()"
  >
    {{ direct.label }}<span
      v-if="direct.count"
      class="menu-count"
    > ({{ direct.count }})</span>
  </button>
  <div
    v-else
    ref="root"
    class="more-menu"
    @keydown="onKeydown"
  >
    <button
      v-if="trigger"
      :id="toggleId"
      ref="toggleButton"
      type="button"
      class="secondary small more-trigger"
      aria-haspopup="menu"
      :aria-expanded="open"
      :data-test="testId"
      @click="toggle"
    >
      <span class="with-icon"><AppIcon
        v-if="triggerIcon"
        :name="triggerIcon"
      />{{ trigger }}</span>
    </button>
    <button
      v-else
      :id="toggleId"
      ref="toggleButton"
      type="button"
      class="more-button"
      :aria-label="label"
      aria-haspopup="menu"
      :aria-expanded="open"
      :data-test="testId"
      @click="toggle"
    >
      <!-- Les trois points de l'iconographie : centrés quelle que soit la police (docs/74, docs/101). -->
      <AppIcon name="more" />
    </button>
    <ul
      v-if="open"
      ref="menu"
      :class="['menu', { up, 'align-left': alignLeft }]"
      role="menu"
      :aria-labelledby="toggleId"
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
          ><AppIcon
            v-if="iconOf(item)"
            :name="iconOf(item)!"
          />{{ item.label }}<span
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
            <AppIcon
              v-if="iconOf(item)"
              :name="iconOf(item)!"
            />{{ item.label }}<span
              v-if="item.count"
              class="menu-count"
            > ({{ item.count }})</span>
          </button>
        </li>
      </template>
    </ul>
  </div>
</template>
