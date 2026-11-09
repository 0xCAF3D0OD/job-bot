<script setup lang="ts">
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";

// Les actions de Postuler (C6, C8) : d'abord le formulaire, puis « J'ai postulé » une fois ouvert. Sur téléphone
// dans la barre du bas, sur ordinateur au pied de la carte « Où postuler » (MODIFICATIONS du 9 novembre, §2.4).
// Plusieurs racines : les règles de la barre du bas (`.action-bar > a`) s'appliquent toujours à ces éléments.
defineProps<{
  link: { url: string; label: string; reopen: string } | null;
  opened: boolean;
  busy: boolean;
  error: string;
}>();
const emit = defineEmits<{ open: []; mark: [] }>();
</script>

<template>
  <p
    v-if="error"
    class="notice error"
    role="alert"
  >
    {{ error }}
  </p>
  <a
    v-if="link && !opened"
    :href="link.url"
    target="_blank"
    rel="noopener noreferrer"
    class="button-link primary-link prep-bar-main"
    data-test="apply"
    @click="emit('open')"
  ><span class="with-icon">{{ link.label }}<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span></a>
  <!-- Déjà fait ailleurs (page rechargée, e-mail, téléphone) : sans rouvrir le formulaire. -->
  <BusyButton
    v-if="link && !opened"
    class="link apply-already"
    :busy="busy"
    busy-label="Enregistrement…"
    data-test="already-applied"
    @click="emit('mark')"
  >
    J'ai déjà postulé
  </BusyButton>
  <template v-else>
    <BusyButton
      class="primary prep-bar-main"
      :busy="busy"
      busy-label="Enregistrement…"
      data-test="mark-applied"
      @click="emit('mark')"
    >
      J'ai postulé
    </BusyButton>
    <a
      v-if="link"
      :href="link.url"
      target="_blank"
      rel="noopener noreferrer"
      class="link apply-reopen"
      data-test="apply"
    >{{ link.reopen }}<span class="visually-hidden"> (nouvel onglet)</span></a>
  </template>
</template>
