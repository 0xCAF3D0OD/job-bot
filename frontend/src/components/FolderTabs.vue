<script setup lang="ts">
import { ref } from "vue";
import type { RouteLocationRaw } from "vue-router";

import CountBadge from "./CountBadge.vue";

// Les onglets « dossier » (LISEZMOI du 17.11, §47) : ils remplacent le contrôle segmenté des pages à vues
// (Candidatures, Envoyées, Rendez-vous, Bilan, étapes de Ma candidature). Des onglets de classeur posés sur une
// ligne : l'actif a le fond de la page, recouvre la ligne et porte une bordure sans le bas ; les autres, plus bas,
// sur un fond neutre, sans bordure ni ombre. Chaque onglet est un lien (les vues ont leur adresse) ; l'actif porte
// aria-selected et aria-current (`current`, « page » ou « step »). Clavier : un seul onglet dans l'ordre Tab, les
// flèches gauche et droite (et Début, Fin) passent d'un onglet à l'autre ; Entrée ouvre l'onglet.
// `count` : la pastille après le libellé, absente à zéro ; `tone` : « accent » (nouvelles offres) ou « orange »
// (rendez-vous à noter).
export type FolderTab = {
  value: string;
  label: string;
  to: RouteLocationRaw;
  test?: string;
  count?: number;
  tone?: "accent" | "orange";
  hint?: string;
};

const props = withDefaults(defineProps<{ tabs: FolderTab[]; selected: string; label: string; current?: "page" | "step" }>(), {
  current: "page",
});
const list = ref<HTMLElement | null>(null);

function move(event: KeyboardEvent): void {
  const keys: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1 };
  const items = [...(list.value?.querySelectorAll<HTMLElement>("[role=tab]") ?? [])];
  const at = items.indexOf(event.target as HTMLElement);
  if (at < 0) return;
  let next: number;
  if (event.key in keys) next = (at + keys[event.key]! + items.length) % items.length;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = items.length - 1;
  else if (event.key === " ") {
    event.preventDefault();
    (event.target as HTMLElement).click();
    return;
  } else return;
  event.preventDefault();
  items[next]!.focus();
}

const isSelected = (tab: FolderTab) => props.selected === tab.value;
</script>

<template>
  <div
    ref="list"
    class="folder-tabs"
    role="tablist"
    :aria-label="label"
    @keydown="move"
  >
    <RouterLink
      v-for="tab in tabs"
      :key="tab.value"
      :to="tab.to"
      role="tab"
      :aria-selected="isSelected(tab)"
      :aria-current="isSelected(tab) ? current : undefined"
      :tabindex="isSelected(tab) || !tabs.some(isSelected) ? 0 : -1"
      :data-test="tab.test ?? `tab-${tab.value}`"
    >
      <slot
        name="tab"
        :tab="tab"
        :selected="isSelected(tab)"
      >
        <span class="folder-tab-label">{{ tab.label }}</span>{{ tab.count ? " " : "" }}<CountBadge
          v-if="tab.count"
          class="tab-count"
          :tone="tab.tone"
          :title="tab.hint"
          :count="tab.count"
        />
      </slot>
    </RouterLink>
  </div>
</template>

<style>
/* Valeurs de la planche (§47) : ligne 1,5 px (#DDD8CC / #38322B), onglet actif 47,5 px au fond de la page, inactif
   42 px sur #ECE8DF / #25201B, texte 15 px (800 / 600), coins de 14 px en haut ; ordinateur 48 et 44 px. Mis sur la
   grille de 4 (audit-grille) : marges de 16 px (14,5 + le bord de 1,5 sur l'actif), 8 px entre le libellé et la
   pastille ; l'actif descend sur la ligne par un décalage (pas de marge négative) ; un inactif de 42 px garde une
   zone de 44 px (::before de 2 px au-dessus, modèle Material 3). */
.folder-tabs, .folder-head { --tab-line: #DDD8CC; --tab-idle: #ECE8DF; --tab-new: var(--primary); --tab-over: 1.5px; }
.folder-tabs {
  --tab-on: 47.5px; --tab-off: 42px; --tab-h: 46px; --tab-pad: var(--space-4); --tab-pad-on: 14.5px; --tab-in: var(--space-2); --tab-radius: 14px; --tab-edge: var(--space-5);
  display: flex; align-items: flex-end; gap: var(--space-1); box-sizing: border-box; height: var(--tab-h);
  margin: 0 calc(var(--space-5) * -1); padding: 0 var(--tab-edge); border-bottom: 1.5px solid var(--tab-line);
}
.folder-tabs > a {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: var(--tab-in); box-sizing: border-box; height: var(--tab-off); padding: 0 var(--tab-pad);
  border-radius: var(--tab-radius) var(--tab-radius) 0 0; background: var(--tab-idle); color: var(--text-secondary);
  font-size: var(--font-label); font-weight: var(--weight-semibold); line-height: var(--leading-none); text-decoration: none; white-space: nowrap;
}
.folder-tabs > a::before { content: ""; position: absolute; top: -2px; left: 0; right: 0; height: 2px; }
.folder-tabs > a[aria-selected="true"] {
  height: var(--tab-on); padding: 0 var(--tab-pad-on); border: 1.5px solid var(--tab-line); border-bottom: 0; transform: translateY(var(--tab-over));
  background: var(--bg); color: var(--text); font-weight: var(--weight-heavy);
}
/* Sous 360 px (CI en 320), les trois onglets et leurs pastilles tiennent sans défiler : marges resserrées. */
@media (max-width: 359px) { .folder-tabs { --tab-pad: var(--space-2); --tab-pad-on: 6.5px; --tab-in: var(--space-1); --tab-edge: var(--space-2); } }
.folder-tabs > a:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.folder-tabs .count-badge { min-width: 20px; height: 20px; background: var(--tab-new); color: #FFFFFF; font-size: var(--font-caption); font-weight: var(--weight-heavy); box-shadow: none; }
.folder-tabs .count-badge.orange { background: #A95A1A; } /* §66 : 5,0:1 avec le blanc. */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) :is(.folder-tabs, .folder-head) { --tab-line: var(--line); --tab-idle: #25201B; --tab-new: #3A5BD9; }
}
:root[data-theme="dark"] :is(.folder-tabs, .folder-head) { --tab-line: var(--line); --tab-idle: #25201B; --tab-new: #3A5BD9; }
@media (min-width: 821px) {
  .folder-tabs { --tab-on: 48px; --tab-off: 44px; margin: 0; padding: 0; }
}
</style>
