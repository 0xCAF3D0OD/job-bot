<script setup lang="ts">
import { ref } from "vue";

import { api } from "../api/client";
import IconButton from "./IconButton.vue";

// « Mon domaine » sur place (docs/43 n° 4) : tant qu'il est vide, ses mots-clés se saisissent
// ici, sans passer par Réglages. Les mêmes mots filtrent Actualités et Formations.
const emit = defineEmits<{ saved: [keywords: string[]] }>();

const value = ref("");
const saving = ref(false);
const error = ref("");

async function save(): Promise<void> {
  const keywords = value.value
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
  if (!keywords.length) return;
  saving.value = true;
  error.value = "";
  try {
    const { data: current } = await api.GET("/api/news/preferences");
    if (!current) throw new Error();
    const { data } = await api.PUT("/api/news/preferences", {
      body: { ...current, domain_keywords: keywords, domain_only: true },
    });
    if (!data) throw new Error();
    emit("saved", data.domain_keywords);
  } catch {
    error.value = "Enregistrement impossible pour l'instant.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <form
    class="domain-field"
    data-test="domain-field"
    @submit.prevent="save"
  >
    <label for="domain-field-input">Ton domaine, en quelques mots-clés</label>
    <div class="domain-field-row">
      <input
        id="domain-field-input"
        v-model="value"
        placeholder="Ton métier, un outil, un diplôme…"
        enterkeyhint="done"
        data-test="domain-field-input"
      >
      <IconButton
        icon="plus"
        type="submit"
        label="Ajouter"
        :disabled="saving || !value.trim()"
        data-test="domain-field-save"
      />
    </div>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
  </form>
</template>
