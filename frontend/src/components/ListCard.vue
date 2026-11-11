<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter, type RouteLocationRaw } from "vue-router";

import { colorIndex, companyPlace, initials } from "../format";
import { isBlankLogo } from "../logoImage";

// La carte d'une liste de Candidatures (maquettes CandidaturesOrdinateur, Candidatures et Envoyees du 7.11.2026),
// la même sur ordinateur et sur téléphone : 104 px de haut, le logo de 44 px, le poste et « entreprise · lieu »
// sur une ligne chacun (coupés par « … »), les puces en bas, une colonne de 76 px à droite (slot `end` : l'anneau
// et son mot, ou le statut d'une candidature). Rien d'autre dans la carte.
// Une offre (lot du 11 novembre au soir, PR 46) met ses étiquettes sous la ligne logo, titre, note, sur toute la
// largeur (slot `below`) : la carte passe alors à la ligne et grandit (104 px au moins).
// Toute la carte est un lien (`to`) ; sans touche de modification, le clic émet `select` à la place, pour que la
// liste garde la main (focus sur la fiche, adresse remplacée…).
const props = withDefaults(
  defineProps<{
    title: string;
    company?: string | null;
    location?: string | null;
    logo?: string | null;
    to: RouteLocationRaw;
    selected?: boolean;
  }>(),
  { company: null, location: null, logo: null, selected: false },
);
const emit = defineEmits<{ select: [] }>();

const router = useRouter();
const href = computed(() => router.resolve(props.to).href);
const name = computed(() => props.company || props.title);
const sub = computed(() => companyPlace(props.company, props.location, true));

// Une image qui ne charge pas, ou vide (un carré blanc générique) : les initiales colorées à la place.
const logoFailed = ref(false);
watch(
  () => props.logo,
  () => (logoFailed.value = false),
);
const showLogo = computed(() => !!props.logo && !logoFailed.value);

function onClick(event: MouseEvent): void {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  event.preventDefault();
  emit("select");
}
</script>

<template>
  <a
    :href="href"
    :class="['list-card', { 'list-card-wrap': $slots.below }]"
    :aria-current="selected ? 'true' : undefined"
    data-test="list-card"
    @click="onClick"
  >
    <span
      :class="['list-card-logo', showLogo ? 'image' : `c${colorIndex(name)}`]"
      aria-hidden="true"
    >
      <img
        v-if="showLogo"
        :src="logo!"
        alt=""
        loading="lazy"
        @load="logoFailed = isBlankLogo($event.target as HTMLImageElement)"
        @error="logoFailed = true"
      >
      <template v-else>{{ initials(name) }}</template>
    </span>
    <span class="list-card-text">
      <span
        class="list-card-title"
        data-test="list-card-title"
      >{{ title }}</span>
      <span
        v-if="sub"
        class="list-card-sub"
      >{{ sub }}</span>
      <span
        v-if="$slots.chips"
        class="list-card-chips"
      ><slot name="chips" /></span>
    </span>
    <span class="list-card-end"><slot name="end" /></span>
    <slot name="below" />
  </a>
</template>

<style>
/* Valeurs de la maquette (HTML de CandidaturesOrdinateur et Envoyees) : hauteur fixe 104, marges 14 et 16, écart
   14, logo 44 aux coins de 12, colonne de droite 76. Sélectionnée : bordure de 2 px bleue, fond bleu très pâle
   (#F5F7FE en clair, mélangé ici pour suivre le sombre), les marges réduites d'1 px pour garder la taille. */
.list-card {
  --card-14: 14px; --card-3: 3px; --card-5: 5px; --card-6: 6px; --card-2: 2px; --card-9: 9px; --card-12: 12px; --card-21: 21px;
  display: flex; align-items: center; gap: var(--card-14); box-sizing: border-box; height: 104px; min-width: 0;
  padding: var(--card-14) var(--space-4); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card);
  color: var(--text); text-decoration: none;
}
.list-card:hover { border-color: var(--field-border); }
/* Version du 9 novembre (D29, §2.9), téléphone : une carte sur la page a un trait de 1,5 px --card-line et 20 px de
   marge intérieure sur les côtés, trait compris (18,5 + 1,5) ; 16 px en haut et en bas (14,5 + 1,5). */
@media (max-width: 820px) {
  .list-card { --card-pad-y: 14.5px; --card-pad-x: 18.5px; padding: var(--card-pad-y) var(--card-pad-x); border: 1.5px solid var(--card-line); }
}
.list-card[aria-current="true"] {
  padding: calc(var(--card-14) - 1px) calc(var(--space-4) - 1px); border: 2px solid var(--primary-graphic);
  background: var(--selected-bg);
}
.list-card-logo {
  flex: none; display: grid; place-items: center; width: var(--target-min); height: var(--target-min); overflow: hidden;
  border-radius: var(--card-12); font-size: var(--font-body); font-weight: var(--weight-bold);
}
.list-card-logo.c0 { background: var(--primary); color: var(--on-primary); }
.list-card-logo.c1 { background: var(--text); color: var(--bg); }
.list-card-logo.c2 { background: var(--peach); color: var(--on-peach); }
.list-card-logo.image { background: var(--logo-paper); }
/* Sombre (maquette CandidaturesSombre) : l'encre devient un carré brun, texte clair ; la pêche garde un texte foncé. */
/* Sombre, téléphone : carré brun foncé (CandidaturesSombre). L'ordinateur inverse (style.css, §12 du 9 novembre). */
@media (max-width: 820px) and (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .list-card-logo.c1 { background: var(--line); color: var(--text); } }
@media (max-width: 820px) { :root[data-theme="dark"] .list-card-logo.c1 { background: var(--line); color: var(--text); } }
.list-card-logo img { width: 100%; height: 100%; object-fit: contain; }
.list-card-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--card-3); }
.list-card-title, .list-card-sub { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.list-card-title { font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--card-21); }
.list-card-sub { font-size: var(--font-small); color: var(--text-secondary); }
.list-card-chips { display: flex; gap: var(--card-6); margin-top: var(--card-5); overflow: hidden; }
.list-card-chips > * {
  flex: none; padding: var(--card-3) var(--card-9); border-radius: var(--radius-sm); white-space: nowrap; font-size: var(--font-caption);
  font-weight: var(--weight-semibold); background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-tertiary);
}
.list-card-chips > .peach { background: var(--peach-soft); color: var(--peach-text); }
.list-card-chips > .blue { background: var(--primary-soft); color: var(--primary-text); }
.list-card-chips > .green { background: var(--success-soft); color: var(--success); }
.list-card-chips > .warn { background: var(--warning-soft); color: var(--warning); }
/* Étiquettes sous le logo (maquettes Candidatures et CandidaturesOrdinateurB du 11 novembre) : deux lignes écartées
   de 8 px, colonnes de 14 px, le logo et le titre centrés sur l'anneau ; 104 px au moins, 14 et 18,5 px de marge. */
.list-card-wrap { --card-pad-x: 18.5px; flex-wrap: wrap; gap: var(--space-2) var(--card-14); height: auto; min-height: 104px; padding: var(--card-14) var(--card-pad-x); }
.list-card-wrap[aria-current="true"] { padding: calc(var(--card-14) - 1px) calc(var(--card-pad-x) - 1px); }
.list-card-wrap .list-card-text { gap: var(--card-2); }
.list-card-wrap > .list-card-chips { flex: 0 0 100%; min-width: 0; margin-top: 0; }
@media (max-width: 820px) { .list-card-wrap { --card-pad-y: 18.5px; padding: var(--card-pad-y) var(--card-pad-x); } }
.list-card-end { flex: none; width: 76px; display: flex; flex-direction: column; align-items: center; text-align: center; }
</style>
