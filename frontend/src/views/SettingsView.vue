<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type SettingsModel } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";

const form = ref<SettingsModel>({
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 10,
});
const loaded = ref(false);
const saving = ref(false);
const message = ref("");

onMounted(async () => {
  const { data } = await api.GET("/api/settings");
  if (data) form.value = data;
  loaded.value = true;
});

async function save(): Promise<void> {
  saving.value = true;
  try {
    const body = { ...form.value, orp_monthly_target: form.value.orp_monthly_target || null };
    const { data } = await api.PUT("/api/settings", { body });
    message.value = data ? "Réglages enregistrés." : "L'enregistrement a échoué : vérifie les valeurs.";
    if (data) form.value = data;
  } catch {
    message.value = "API injoignable.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <PageHero
    eyebrow="Réglages"
    title="Tes réglages"
    subtitle="Objectif de l'ORP, notifications et budget de l'IA."
  />
  <section class="band">
    <div class="container narrow">
      <form
        v-if="loaded"
        class="form-card"
        data-test="settings-form"
        @submit.prevent="save"
      >
        <fieldset>
          <legend><label for="orp">Objectif mensuel de l'ORP</label></legend>
          <p class="hint">
            Nombre de candidatures demandé par ton conseiller. Vide si tu ne le connais pas encore.
          </p>
          <div class="inline-field">
            <input
              id="orp"
              v-model.number="form.orp_monthly_target"
              type="number"
              min="1"
              max="100"
            >
            <span>candidatures par mois</span>
          </div>
        </fieldset>
        <fieldset>
          <legend><label for="threshold">Seuil de notification</label></legend>
          <p class="hint">
            Utilisé à partir de la 0.4 : tu es prévenu pour les offres notées au moins à ce score.
          </p>
          <div class="inline-field">
            <input
              id="threshold"
              v-model.number="form.notify_score_threshold"
              type="number"
              min="0"
              max="100"
              required
            >
            <span>/ 100</span>
          </div>
        </fieldset>
        <fieldset>
          <legend><label for="budget">Plafond mensuel du coût de l'IA</label></legend>
          <p class="hint">
            Au-delà, les notes sont mises en pause jusqu'au mois suivant (0.4).
          </p>
          <div class="inline-field">
            <input
              id="budget"
              v-model.number="form.llm_monthly_budget_chf"
              type="number"
              min="0"
              max="1000"
              step="0.5"
              required
            >
            <span>CHF</span>
          </div>
        </fieldset>
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            :disabled="saving"
            data-test="save-settings"
          >
            Enregistrer <AppIcon name="chevron" />
          </button>
          <span
            v-if="message"
            role="status"
            class="muted"
          >{{ message }}</span>
        </div>
      </form>
    </div>
  </section>
</template>
