<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Identity } from "../api/client";
import { usePhone } from "../composables/usePhone";
import CopyButton from "./CopyButton.vue";
import DisclosureRow from "./DisclosureRow.vue";

// Fiche « Pour le formulaire » (docs/25 §5) : chaque valeur à copier dans le formulaire en
// ligne de l'employeur, dans l'ordre habituel de ces formulaires. Une ligne par champ (maquette
// Preparer, étape 7c) : le nom en petit, la valeur, et « Copier » qui devient « Copié ».
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
    ["NPA", who.postcode],
    ["Localité", who.city],
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
// d'abord, les autres sous « Autres champs », replié.
const FIRST = new Set(["Prénom", "Nom", "E-mail", "Téléphone", "Localité"]);
const shown = computed(() => (phone.value ? rows.value.filter(([label]) => FIRST.has(label)) : rows.value));
const more = computed(() => (phone.value ? rows.value.filter(([label]) => !FIRST.has(label)) : []));

const missing = computed(() => {
  const who = identity.value;
  if (!who) return false;
  return !who.name || !who.email || !who.phone;
});
</script>

<template>
  <div
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
          {{ value }}
        </dd>
        <CopyButton
          :value="value"
          :text="label"
          test-id="sheet-copy"
        />
      </div>
    </dl>
    <DisclosureRow
      v-if="more.length"
      title="Autres champs"
      :value="String(more.length)"
      class="form-sheet-more"
      data-test="sheet-more"
    >
      <dl>
        <div
          v-for="[label, value] in more"
          :key="label"
          class="form-sheet-row"
        >
          <dt>{{ label }}</dt>
          <dd :class="{ 'form-sheet-long': value.length > 80 }">
            {{ value }}
          </dd>
          <CopyButton
            :value="value"
            :text="label"
            test-id="sheet-copy"
          />
        </div>
      </dl>
    </DisclosureRow>
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
/* « Autres champs » : une ligne de la fiche comme les autres (trait du haut, même hauteur), pas une carte dans la
   carte ; le titre en gras comme les valeurs. */
.form-sheet-more { border: 0; border-top: 1px solid var(--line-soft); border-radius: 0; background: none; }
.form-sheet-more :deep(.disclosure-row) { min-height: 3.25rem; padding: var(--space-1) var(--space-4); font-size: var(--font-body); font-weight: var(--weight-bold); }
.form-sheet-more :deep(.disclosure-value) { font-weight: var(--weight-regular); color: var(--text-secondary); }
</style>
