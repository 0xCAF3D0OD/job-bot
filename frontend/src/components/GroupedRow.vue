<script setup lang="ts">
import { computed, useId } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Une ligne de liste groupée (règles §4) : icône facultative, titre, phrase grise, puis à droite une
// valeur et un chevron, ou une commande (slot `end`, un interrupteur). Toute la ligne est la cible,
// 48 px de haut au moins :
// - `to` ou `href` : un lien, avec chevron ;
// - `button` : un bouton (événement click), avec chevron ;
// - `label` : une étiquette ; la radio ou la case va dans le slot `start` (WCAG 2.5.8) ;
// - sinon, une ligne d'information.
// `current` : l'entrée affichée à côté (liste et détail, Réglages sur ordinateur) : aria-current="page" et la
// pastille de sélection (Sélection unique, §4).
const props = withDefaults(
  defineProps<{ title: string; description?: string; icon?: IconName; value?: string; to?: RouteLocationRaw; href?: string; button?: boolean; label?: boolean; chevron?: boolean; current?: boolean }>(),
  { description: "", icon: undefined, value: "", to: undefined, href: undefined, button: false, label: false, chevron: undefined, current: false },
);
const emit = defineEmits<{ click: [event: MouseEvent] }>();
const descriptionId = useId();
const tag = computed(() => (props.to ? "RouterLink" : props.href ? "a" : props.button ? "button" : props.label ? "label" : "div"));
const showChevron = computed(() => props.chevron ?? Boolean(props.to || props.href || props.button));
</script>

<template>
  <li class="grouped-item">
    <component
      :is="tag"
      class="grouped-row"
      :class="{ 'grouped-row-action': tag !== 'div', 'grouped-row-current': current }"
      :aria-current="current ? 'page' : undefined"
      :to="to"
      :href="href"
      :type="tag === 'button' ? 'button' : undefined"
      :aria-describedby="description && tag !== 'label' ? descriptionId : undefined"
      @click="tag === 'button' && emit('click', $event)"
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
          v-if="description"
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
