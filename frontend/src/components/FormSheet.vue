<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Identity } from "../api/client";

// Fiche « Pour le formulaire » (docs/25 §5) : chaque valeur à copier dans le formulaire en
// ligne de l'employeur, dans l'ordre habituel de ces formulaires.
const props = defineProps<{ letterText?: string | null; letterId?: number | null; cvId?: number | null }>();

const identity = ref<Identity | null>(null);
const copied = ref<string | null>(null);

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

const missing = computed(() => {
  const who = identity.value;
  if (!who) return false;
  return !who.name || !who.email || !who.phone;
});

async function copy(label: string, value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    copied.value = label;
    setTimeout(() => {
      if (copied.value === label) copied.value = null;
    }, 1500);
  } catch {
    copied.value = null;
  }
}
</script>

<template>
  <div
    class="form-sheet"
    data-test="form-sheet"
  >
    <p class="hint">
      À recopier dans le formulaire de l'employeur. Joins le CV et la lettre en PDF.
    </p>
    <p
      v-if="letterId || cvId"
      class="form-sheet-files"
    >
      <a
        v-if="cvId"
        class="link"
        :href="`/api/cvs/${cvId}/pdf`"
        download
        data-test="sheet-cv"
      >CV (PDF)</a>
      <a
        v-if="letterId"
        class="link"
        :href="`/api/letters/${letterId}/pdf`"
        download
        data-test="sheet-letter"
      >Lettre (PDF)</a>
    </p>
    <dl>
      <template
        v-for="[label, value] in rows"
        :key="label"
      >
        <dt>{{ label }}</dt>
        <dd>
          <span :class="{ 'form-sheet-long': value.length > 80 }">{{ value }}</span>
          <button
            type="button"
            class="link"
            data-test="sheet-copy"
            @click="copy(label, value)"
          >
            {{ copied === label ? "Copié" : "Copier" }}
          </button>
        </dd>
      </template>
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
