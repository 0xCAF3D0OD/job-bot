<script setup lang="ts">
import { ref } from "vue";

import ProfileCompletionForm, { type CompletionSection } from "./ProfileCompletionForm.vue";
import SidePanel from "./SidePanel.vue";

// Le formulaire « Complétons ton profil » en panneau (prompt du 10 novembre, PR 17, points 4 et 5) : ouvert depuis une
// offre pas encore notée faute de profil (« Compléter mon profil »), ou depuis Préparer (« Ajouter une expérience »,
// ou le nom et l'adresse qui manquent à la lettre). À l'enregistrement, la page reprend où elle en était.
withDefaults(defineProps<{ open: boolean; title: string; sections?: CompletionSection[]; roles?: string[] }>(), {
  sections: () => ["experiences", "languages", "identity"],
  roles: () => [],
});
const emit = defineEmits<{ close: []; saved: [] }>();
const form = ref<InstanceType<typeof ProfileCompletionForm> | null>(null);

async function save(): Promise<void> {
  if (!form.value || form.value.saving) return;
  if (await form.value.save()) emit("saved");
}
</script>

<template>
  <SidePanel
    :open="open"
    :title="title"
    :width="480"
    @close="emit('close')"
  >
    <ProfileCompletionForm
      v-if="open"
      ref="form"
      :sections="sections"
      :roles="roles"
    />
    <div class="pcp-actions">
      <button
        type="button"
        class="primary"
        :aria-disabled="form?.saving ? 'true' : undefined"
        data-test="completion-save"
        @click="save"
      >
        Enregistrer
      </button>
      <button
        type="button"
        class="secondary"
        @click="emit('close')"
      >
        Annuler
      </button>
    </div>
  </SidePanel>
</template>

<style>
.pcp-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); margin-top: var(--space-8); }
</style>
