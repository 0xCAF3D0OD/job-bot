<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { api, type Identity } from "../api/client";
import { usePhone } from "../composables/usePhone";
import CopyButton from "./CopyButton.vue";
import AppIcon from "./AppIcon.vue";
import { phoneDisplay } from "../format";

// Fiche « Pour le formulaire » (docs/25 §5) : chaque valeur à copier dans le formulaire en
// ligne de l'employeur, dans l'ordre habituel de ces formulaires. Une ligne par champ (maquette
// Preparer, étape 7c) : le nom en petit, la valeur, et « Copier » qui devient « Copié ». Sur ordinateur
// (MODIFICATIONS du 9 novembre, §1) : l'icône seule dans un cercle, « Copier : prénom » lu, « Copier » au survol.
const props = defineProps<{ letterText?: string | null }>();

const identity = ref<Identity | null>(null);
const { phone } = usePhone();

onMounted(async () => {
  const { data } = await api.GET("/api/identity");
  identity.value = data ?? null;
});

// « Kevin Di Nocera » : le prénom est le premier mot, le nom le reste.
function split(name: string | null | undefined): [string, string] {
  const words = (name ?? "").trim().split(/\s+/).filter(Boolean);
  return words.length > 1 ? [words[0] ?? "", words.slice(1).join(" ")] : ["", words[0] ?? ""];
}

const rows = computed(() => {
  const who = identity.value;
  if (!who) return [];
  const [first, last] = split(who.name);
  const all: [string, string | null | undefined][] = [
    ["Prénom", first],
    ["Nom", last],
    ["E-mail", who.email],
    ["Téléphone", who.phone],
    ["Rue et numéro", who.street],
    // Sur ordinateur, une seule ligne « NPA et localité » (maquette PreparerOrdinateurPostuler).
    ...(phone.value
      ? ([["NPA", who.postcode], ["Localité", who.city]] as [string, string | null | undefined][])
      : ([["NPA et localité", [who.postcode, who.city].filter(Boolean).join(" ")]] as [string, string][])),
    ["Pays", who.city ? "Suisse" : null],
    ["LinkedIn", who.linkedin],
    ["Site personnel", who.website],
    ["Disponibilité", who.availability],
    ["Prétentions salariales", who.salary],
    ["Permis de travail", who.permit],
    ["Lettre de motivation (texte)", props.letterText],
  ];
  return all.filter((row): row is [string, string] => Boolean(row[1]?.trim()));
});
// Sur téléphone (maquette Preparer, Kevin 2026-11-06) : les cinq champs de presque tous les formulaires
// d'abord ; les autres dans « Si le formulaire le demande » (planche MaCandidatureV2, 14.11 ; avant : « Autres
// champs », replié).
const FIRST = new Set(["Prénom", "Nom", "E-mail", "Téléphone", "Localité"]);
const shown = computed(() => (phone.value ? rows.value.filter(([label]) => FIRST.has(label)) : rows.value));
const more = computed(() => (phone.value ? rows.value.filter(([label]) => !FIRST.has(label)) : []));

// Téléphone : toute la ligne copie sa valeur (« À copier · touche une ligne ») ; la coche et « Copié » 2 s, annoncés.
const copied = ref("");
let timer: ReturnType<typeof setTimeout> | undefined;
async function copyRow(label: string, value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    return;
  }
  copied.value = label;
  clearTimeout(timer);
  timer = setTimeout(() => (copied.value = ""), 2000);
}
onUnmounted(() => clearTimeout(timer));
// Les prétentions salariales sont marquées d'un cadenas (planche) : une valeur à ne donner que si on la demande.
const PRIVATE = new Set(["Prétentions salariales"]);

const missing = computed(() => {
  const who = identity.value;
  if (!who) return false;
  return !who.name || !who.email || !who.phone;
});
</script>

<template>
  <!-- Téléphone (planche MaCandidatureV2, état « formulaire ») : deux cartes, chaque ligne est un bouton qui copie. -->
  <div
    v-if="phone"
    class="form-sheet apl-sheet"
    data-test="form-sheet"
  >
    <section
      v-for="group in [{ key: 'first', title: 'À copier · touche une ligne', items: shown }, { key: 'more', title: 'Si le formulaire le demande', items: more }].filter((g) => g.items.length)"
      :key="group.key"
      class="apl-card"
      :aria-label="group.key === 'first' ? 'À recopier sur le formulaire' : 'Si le formulaire le demande'"
      :data-test="group.key === 'more' ? 'sheet-more' : undefined"
    >
      <h2 class="apl-cap">
        {{ group.title }}
      </h2>
      <button
        v-for="[label, value] in group.items"
        :key="label"
        type="button"
        class="apl-row"
        data-test="sheet-copy"
        @click="copyRow(label, value)"
      >
        <span class="apl-row-text">
          <span class="apl-row-label">{{ label }}</span>
          <span :class="['apl-row-value', { 'form-sheet-long': value.length > 80 }]">{{ label === "Téléphone" ? phoneDisplay(value) : value }}<AppIcon
            v-if="PRIVATE.has(label)"
            name="lock"
            class="apl-row-lock"
          /></span>
        </span>
        <AppIcon
          :name="copied === label ? 'done' : 'copy'"
          :class="['apl-row-icon', { done: copied === label }]"
        />
        <span class="visually-hidden">{{ copied === label ? "Copié" : `Copier : ${label.toLowerCase()}` }}</span>
      </button>
    </section>
    <span
      class="visually-hidden"
      role="status"
    >{{ copied ? "Copié" : "" }}</span>
    <p
      v-if="missing"
      class="hint"
    >
      Il manque des coordonnées :
      <RouterLink
        to="/profil?onglet=coordonnees"
        class="link"
      >
        compléter dans Profil
      </RouterLink>
    </p>
  </div>
  <div
    v-else
    class="form-sheet"
    data-test="form-sheet"
  >
    <dl>
      <div
        v-for="[label, value] in shown"
        :key="label"
        class="form-sheet-row"
      >
        <dt>{{ label }}</dt>
        <dd :class="{ 'form-sheet-long': value.length > 80 }">
          {{ label === "Téléphone" ? phoneDisplay(value) : value }}
        </dd>
        <CopyButton
          :value="value"
          :label="`Copier : ${label.toLowerCase()}`"
          test-id="sheet-copy"
        />
      </div>
    </dl>
    <p
      v-if="missing"
      class="hint"
    >
      Il manque des coordonnées :
      <RouterLink
        to="/profil?onglet=coordonnees"
        class="link"
      >
        compléter dans Profil
      </RouterLink>
    </p>
  </div>
</template>

<style scoped>
/* Planche MaCandidatureV2 (état « formulaire ») : libellé 13/700 gris au-dessus de la valeur 15 ; lignes de 64 px,
   12 px en haut et en bas (§9 du 14.11, la planche dessinait 56 et 8) ; l'icône copier 20 px grise à droite. */
.apl-sheet { display: contents; }
.apl-row { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: 4rem; padding: var(--space-3) var(--space-4); box-sizing: border-box; border: 0; border-top: 1px solid var(--line-soft); background: transparent; color: var(--text); font: inherit; text-align: left; white-space: normal; cursor: pointer; }
.apl-row:hover { background: var(--selected-bg); }
.apl-row:last-child { border-radius: 0 0 var(--apl-radius, 16px) var(--apl-radius, 16px); }
.apl-row-text { flex: 1; min-width: 0; }
.apl-row-label { display: block; font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.apl-row-value { --apl-6: 6px; display: flex; align-items: center; gap: var(--apl-6); font-size: var(--font-label); overflow-wrap: anywhere; }
.apl-row-value.form-sheet-long { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.apl-row-lock { flex: none; width: 14px; height: 14px; color: var(--text-secondary); }
.apl-row-icon { flex: none; width: var(--space-5); height: var(--space-5); color: var(--text-secondary); }
.apl-row-icon.done { color: var(--success); }
.apl-sheet > .hint { margin: 0 var(--space-5) var(--space-4); }
</style>
