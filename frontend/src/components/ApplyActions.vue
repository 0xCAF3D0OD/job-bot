<script setup lang="ts">
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";

// Les actions de Postuler (C6, C8) : d'abord le formulaire, puis « J'ai postulé » une fois ouvert. Sur téléphone
// dans la barre du bas, sur ordinateur au pied de la carte « Où postuler » (MODIFICATIONS du 9 novembre, §2.4).
// Plusieurs racines : sur téléphone, la barre du bas (bottom-bar.css) les range sur une ligne, « J'ai déjà postulé » (ou
// « Rouvrir … ») à contour à gauche, l'action principale pleine à droite (Kevin, 19.11.2026).
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
    class="notice error bb-note"
    role="alert"
  >
    {{ error }}
  </p>
  <a
    v-if="link && !opened"
    :href="link.url"
    target="_blank"
    rel="noopener noreferrer"
    class="button-link primary-link prep-bar-main bb-main"
    data-test="apply"
    @click="emit('open')"
  ><span class="with-icon">{{ link.label }}<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span></a>
  <!-- Déjà fait ailleurs (page rechargée, e-mail, téléphone) : sans rouvrir le formulaire. -->
  <BusyButton
    v-if="link && !opened"
    class="link apply-already bb-alt"
    :busy="busy"
    busy-label="Enregistrement…"
    data-test="already-applied"
    @click="emit('mark')"
  >
    J’ai déjà postulé
  </BusyButton>
  <template v-else>
    <BusyButton
      class="primary prep-bar-main bb-main"
      :busy="busy"
      busy-label="Enregistrement…"
      data-test="mark-applied"
      @click="emit('mark')"
    >
      J’ai postulé
    </BusyButton>
    <a
      v-if="link"
      :href="link.url"
      target="_blank"
      rel="noopener noreferrer"
      class="link apply-reopen bb-alt"
      data-test="apply"
    >{{ link.reopen }}<span class="visually-hidden"> (nouvel onglet)</span></a>
  </template>
</template>
