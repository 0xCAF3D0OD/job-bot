<script setup lang="ts">
// Gabarit « deux colonnes » d'un détail sur ordinateur (MODIFICATIONS du 8 novembre au soir, §2) : la colonne
// principale, puis la colonne d'appui nommée. L'ordre du DOM suit l'ordre de lecture (WCAG 1.3.2) : pas d'`order`.
// Sur téléphone, le gabarit ne sert pas : le détail garde une seule colonne.
withDefaults(defineProps<{ asideLabel: string; narrow?: boolean }>(), { narrow: false });
</script>

<template>
  <div
    :class="['detail-columns', { 'detail-columns-narrow': narrow }]"
    data-test="detail-columns"
  >
    <div
      class="detail-columns-main"
      data-test="detail-columns-main"
    >
      <slot name="main" />
    </div>
    <aside
      class="detail-columns-aside"
      :aria-label="asideLabel"
      data-test="detail-columns-aside"
    >
      <slot name="aside" />
    </aside>
  </div>
</template>

<style>
/* Valeurs du §2 : grille 1fr + 240 (560 + 240 aux rendez-vous), 48 d'écart ; sections de 32/36 séparées par un trait ;
   colonne d'appui à 40 du trait de gauche ; titres de 18/24 en 700, sur-titres de 13 en capitales. */
.detail-columns {
  --cols-aside: 240px; --cols-gap: 48px; --cols-aside-pad: 40px; --cols-pad-top: 32px; --cols-pad-bottom: 36px; --cols-top: 12px;
  --cols-title: 24px; --cols-dd-gap: 2px;
  display: grid; grid-template-columns: minmax(0, 1fr) var(--cols-aside); column-gap: var(--cols-gap);
  margin-top: var(--cols-top); border-top: 1px solid var(--line-soft);
}
.detail-columns-narrow { grid-template-columns: minmax(0, 560px) var(--cols-aside); justify-content: space-between; }
.detail-columns-main, .detail-columns-aside { min-width: 0; }
.detail-columns-aside { padding-left: var(--cols-aside-pad); border-left: 1px solid var(--line-soft); }
.detail-section { margin: 0; padding: var(--cols-pad-top) 0 var(--cols-pad-bottom); border-top: 1px solid var(--line-soft); }
:is(.detail-columns-main, .detail-columns-aside) > .detail-section:first-child { border-top: 0; }
.detail-section > h3 { margin: 0 0 var(--space-4); font-size: var(--font-title); line-height: var(--cols-title); font-weight: var(--weight-bold); }
.detail-overline { margin: 0 0 var(--space-4); font-size: var(--label-caps); font-weight: var(--weight-bold); letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); }
.detail-links { display: flex; flex-direction: column; gap: var(--space-1); margin: 0; padding: 0; list-style: none; }
.detail-link { display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--target-min); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-semibold); text-decoration: none; }
.detail-link:hover { text-decoration: underline; }
.detail-link .icon { width: 15px; height: 15px; }
.detail-link.strong { font-weight: var(--weight-bold); }
.detail-link.strong .icon { width: 18px; height: 18px; }
.detail-list { margin: 0; }
.detail-list > div { padding: var(--space-3) 0; }
.detail-list > div + div { border-top: 1px solid var(--line-soft); }
.detail-list dt { font-size: var(--font-small); color: var(--text-secondary); }
.detail-list dd { margin: var(--cols-dd-gap) 0 0; font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
