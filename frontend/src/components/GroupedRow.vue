<script setup lang="ts">
import { computed, useId } from "vue";
import { type RouteLocationRaw, useRouter } from "vue-router";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Une ligne de liste groupée (règles §4) : icône facultative, titre, phrase grise, puis à droite une
// valeur en pastille et un chevron, ou une commande (slot `end`, un interrupteur). Toute la ligne est la cible,
// 48 px de haut au moins :
// - `to` ou `href` : un lien, avec chevron ;
// - `button` : un bouton (événement click), avec chevron ;
// - `label` : une étiquette ; la radio ou la case va dans le slot `start` (WCAG 2.5.8) ;
// - sinon, une ligne d'information.
// Une ligne qui mène ailleurs (`to`, `href`) n'a jamais de phrase grise : toutes ont la même hauteur, l'aperçu va
// dans la pastille de `value` (2026-11-05, Kevin). La phrase reste pour un réglage ou une action qui s'explique.
// `current` : l'entrée affichée à côté (liste et détail, Réglages sur ordinateur) : aria-current="page" et la
// pastille de sélection (Sélection unique, §4). `busy` : un bouton dont l'action tourne, aria-disabled et
// aria-busy (il garde le focus) ; le clic n'émet rien.
const props = withDefaults(
  defineProps<{ title: string; description?: string; icon?: IconName; value?: string; to?: RouteLocationRaw; href?: string; button?: boolean; label?: boolean; chevron?: boolean; current?: boolean; busy?: boolean }>(),
  { description: "", icon: undefined, value: "", to: undefined, href: undefined, button: false, label: false, chevron: undefined, current: false, busy: false },
);
const emit = defineEmits<{ click: [event: MouseEvent] }>();
const descriptionId = useId();
// Un lien interne est un vrai <a href> (atteignable au Tab, ouvrable dans un nouvel onglet) ; le routeur
// prend le clic simple. Pas de RouterLink : il marquerait « page » toute ligne qui ne diffère que par la
// query (/reglages?rubrique=…), seul `current` le décide.
const router = useRouter();
const tag = computed(() => (props.to || props.href ? "a" : props.button ? "button" : props.label ? "label" : "div"));
const linkHref = computed(() => (props.to ? router.resolve(props.to).href : props.href));
const attrs = computed(() =>
  tag.value === "a"
    ? { href: linkHref.value }
    : tag.value === "button"
      ? { type: "button", "aria-disabled": props.busy ? "true" : undefined, "aria-busy": props.busy ? "true" : undefined }
      : {},
);
function onClick(event: MouseEvent): void {
  if (tag.value === "button" && !props.busy) emit("click", event);
  if (!props.to || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  void router.push(props.to);
}
const shownDescription = computed(() => (tag.value === "a" ? "" : props.description));
const showChevron = computed(() => props.chevron ?? Boolean(props.to || props.href || props.button));
</script>

<template>
  <li class="grouped-item">
    <component
      :is="tag"
      class="grouped-row"
      :class="{ 'grouped-row-action': tag !== 'div', 'grouped-row-current': current }"
      :aria-current="current ? 'page' : undefined"
      v-bind="attrs"
      :aria-describedby="shownDescription && tag !== 'label' ? descriptionId : undefined"
      @click="onClick"
    >
      <slot name="start" />
      <AppIcon
        v-if="icon"
        :name="icon"
        class="grouped-icon"
      />
      <span class="grouped-text">
        <span class="grouped-row-title">{{ title }}</span>
        <span
          v-if="shownDescription"
          :id="descriptionId"
          class="grouped-row-description"
        >{{ description }}</span>
      </span>
      <span
        v-if="value"
        class="grouped-value"
      >{{ value }}</span>
      <slot name="end" />
      <AppIcon
        v-if="showChevron"
        name="chevron"
        class="grouped-chevron"
      />
    </component>
  </li>
</template>
