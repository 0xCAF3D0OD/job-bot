<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import type { RouteLocationRaw } from "vue-router";

import { dateInSentence } from "../dates";
import { dayKey, ofMonth } from "../format";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";

// Le rappel des justificatifs en haut de l'Accueil du téléphone (§57 du 17.11, planches AccueilJustificatif et
// AccueilJustificatifSombre ; Kevin 17.11, 13 h 21). Un îlot à 8 px des bords, posé par-dessus le haut de l'écran,
// avec les jetons des feuilles en îlot (#828) : rayon --panel-float-r, ombre --panel-float-shadow, fond --surface,
// trait --panel-float-line en sombre. role="status" : lu sans prendre le focus.
// Montré seulement quand des justificatifs sont à remettre ou en retard (la page ne le pose qu'avec orp_due_month,
// que le serveur vide dès que le mois est « Déjà remis »), et au plus une fois par jour : la date du jour où il a été
// montré est gardée dans ce navigateur. « Fermer pour aujourd'hui » le retire ; il revient le lendemain.
const props = defineProps<{
  /** Le mois à remettre (« 2026-10 »). */
  month: string;
  /** L'échéance (« 2026-11-05 »), reportée au jour ouvrable du canton par le serveur. */
  due: string;
  /** Le jour d'aujourd'hui passé l'échéance. */
  late: boolean;
  /** La page ORP, où « Exporter » mène. */
  to: RouteLocationRaw;
}>();

const KEY = "jobA1.rappel-orp";
const open = ref(false);

onMounted(() => {
  const today = dayKey(new Date().toISOString());
  try {
    if (localStorage.getItem(KEY) === today) return;
    localStorage.setItem(KEY, today);
  } catch {
    // Stockage refusé : le rappel se montre à chaque ouverture, la croix le ferme.
  }
  open.value = true;
});

// Le rappel ne cache jamais un bandeau du haut, maintenance ou démo (K33 de l'audit du 17.11) : il se pose 8 px sous le
// dernier, remonte avec lui quand la page défile, puis reste à sa place habituelle, 8 px sous le haut de l'écran. Un
// bandeau qui arrive après le rappel (la maintenance se lit au démarrage) le déplace aussi.
const top = ref<string | undefined>(undefined);
let frame = 0;
function place(): void {
  cancelAnimationFrame(frame);
  frame = requestAnimationFrame(() => {
    const bottoms = [...document.querySelectorAll<HTMLElement>(".maintenance-bypass, .demo-banner")].map((el) => el.getBoundingClientRect().bottom);
    const bottom = Math.max(0, ...bottoms);
    top.value = bottom > 0 ? `${Math.round(bottom) + 8}px` : undefined;
  });
}
const banners = new MutationObserver(place);
watch(open, async (isOpen) => {
  globalThis.removeEventListener("scroll", place);
  banners.disconnect();
  if (!isOpen) return;
  await nextTick();
  place();
  globalThis.addEventListener("scroll", place, { passive: true });
  const root = document.getElementById("app");
  if (root) banners.observe(root, { childList: true });
});
onUnmounted(() => {
  globalThis.removeEventListener("scroll", place);
  banners.disconnect();
  cancelAnimationFrame(frame);
});

const dueDay = computed(() => dateInSentence(`${props.due}T12:00:00`));
// « Échéance passée le 5 novembre » (planche) ; avant l'échéance, la phrase de la tâche n°1 (« À remettre avant le 5 décembre »).
const detail = computed(() => {
  if (props.late) return `Échéance passée ${dueDay.value}`;
  return props.due === dayKey(new Date().toISOString()) ? "À remettre aujourd’hui" : `À remettre avant ${dueDay.value}`;
});
</script>

<template>
  <div
    v-if="open"
    class="orp-reminder"
    :style="top ? { top } : undefined"
    role="status"
    data-test="orp-reminder"
  >
    <span aria-hidden="true"><AppIcon name="alert-circle" /></span>
    <span class="orp-reminder-text">
      <b>Justificatifs {{ ofMonth(month) }} à remettre</b>
      <span>{{ detail }}</span>
    </span>
    <RouterLink
      :to="to"
      data-test="orp-reminder-export"
    >
      Exporter
    </RouterLink>
    <IconButton
      icon="close"
      label="Fermer pour aujourd’hui"
      data-test="orp-reminder-close"
      @click="open = false"
    />
  </div>
</template>

<style>
/* Planches AccueilJustificatif (+ Sombre) : îlot 12/8/12/14 au-dessus de la barre du haut, rond 40 px, 15/20 gras puis
   13/18 brun, « Exporter » 44 px bleu ; la croix est le bouton rond commun (44 px sur téléphone). */
.orp-reminder {
  --orp-r-14: 14px; --orp-r-13: 13px; --orp-r-18: 18px; --orp-r-20: 20px;
  position: fixed; top: calc(var(--space-2) + env(safe-area-inset-top)); left: var(--space-2); right: var(--space-2); z-index: 60;
  display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-2) var(--space-3) var(--orp-r-14);
  border: 1px solid var(--panel-float-line); border-radius: var(--panel-float-r); background: var(--surface); box-shadow: var(--panel-float-shadow);
}
.orp-reminder > span:first-child { flex: none; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: var(--peach-soft); color: var(--peach-text); }
.orp-reminder > span:first-child .icon { width: 20px; height: 20px; }
.orp-reminder-text { flex: 1; min-width: 0; }
.orp-reminder b { display: block; font-size: var(--font-label); line-height: var(--orp-r-20); }
.orp-reminder b + span { display: block; font-size: var(--orp-r-13); line-height: var(--orp-r-18); color: var(--peach-text); }
.orp-reminder a { display: flex; align-items: center; height: var(--target-min); padding: 0 var(--orp-r-14); border-radius: var(--radius-pill); background: var(--action); color: var(--on-action); font-size: var(--font-small); font-weight: var(--weight-bold); text-decoration: none; }
</style>
