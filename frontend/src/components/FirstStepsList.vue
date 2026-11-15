<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Today } from "../api/client";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";

// Les premiers pas en cinq lignes (§23 du 15.11, planches AujourdhuiOrdinateurNouveau et AccueilNouveau, option B de
// Kevin) : une seule forme pour l'ordinateur et le téléphone. Une étape faite : coche verte et « Fait ». La prochaine :
// son numéro en bleu et le seul bouton plein de l'écran. Les autres, grisées, sans bouton. Garder et envoyer attendent
// la première offre. Ordinateur : cartes blanches de 88 px, 12 px d'écart ; téléphone : lignes de 72 px séparées par
// un trait, le bouton en pleine largeur sous la ligne.
type Key = Today["first_steps"][number]["key"];
const props = defineProps<{
  steps: Today["first_steps"];
  summary: Today["first_steps_summary"];
  hasOffers: boolean;
  offerId: number | null;
  // Des offres du jour sont à trier : « Garder » ouvre l'écran de tri.
  pickReady: boolean;
  phone?: boolean;
}>();
const emit = defineEmits<{ dismiss: [] }>();

const next = computed(() => props.steps.find((s) => !s.done) ?? null);
const doneCount = computed(() => props.steps.filter((s) => s.done).length);
const waiting = (key: Key) => (key === "keep" || key === "send") && !props.hasOffers;

function criteriaLine(): string {
  const s = props.summary;
  const rate = s?.min_rate ? `${s.min_rate} à 100 %` : null;
  return [s?.trade, s?.place, rate].filter(Boolean).join(" · ") || "Critères enregistrés";
}

// Les textes des planches pour les états dessinés ; pour une étape à faire autre que l'alerte (non dessinée), les
// mots de l'ancienne carte.
function row(key: Key, done: boolean) {
  const skills = props.summary?.skills ?? 0;
  const preparation = props.offerId ? `/candidatures/offres/${props.offerId}/preparer` : "/candidatures/offres";
  const rows: Record<Key, { title: string; sub: string; action: string; to: RouteLocationRaw }> = {
    cv: done
      ? { title: "Ton CV est lu", sub: skills ? `${plural(skills, "compétence reprise", "compétences reprises")}` : "CV déposé", action: "", to: "" }
      : { title: "Dépose ton CV", sub: "jobA1 en tire tes compétences.", action: "Déposer mon CV", to: "/profil" },
    criteria: done
      ? { title: "Tes critères sont réglés", sub: criteriaLine(), action: "", to: "" }
      : { title: "Règle tes critères", sub: "jobA1 trie les offres avec tes critères.", action: "Régler mes critères", to: "/profil" },
    alerts: done
      ? { title: "Ta première alerte est créée", sub: "jobup · chaque jour", action: "", to: "" }
      : { title: "Créer ta première alerte", sub: "jobup : 2 minutes", action: "Créer mon alerte", to: { path: "/bienvenue", query: { etape: "alerte" } } },
    keep: {
      title: "Garder tes premières offres",
      sub: "Celles qui te vont passent en « À préparer ».",
      action: "Trier mes offres",
      to: props.pickReady ? { name: "triage" } : "/candidatures/offres",
    },
    send: { title: "Préparer et envoyer une candidature", sub: "Lettre et CV adaptés à l’offre gardée.", action: "Préparer", to: preparation },
  };
  const out = rows[key];
  if (!done && waiting(key)) {
    // Les trois premières faites sans offre : l'étape 4 dit quand la première arrive.
    out.sub = key === "keep" && doneCount.value >= 3 ? "Ta première offre arrive après la prochaine collecte" : "Dès ta première offre";
  }
  return out;
}

const lines = computed(() =>
  props.steps.map((step, i) => {
    const current = step === next.value && !waiting(step.key);
    return { ...step, n: i + 1, current, locked: !step.done && !current, ...row(step.key, step.done) };
  }),
);
</script>

<template>
  <section
    v-if="next"
    :class="['fs', { 'fs-phone': phone }]"
    aria-labelledby="first-steps-title"
    data-test="first-steps"
    :data-step="next.key"
  >
    <div class="fs-head">
      <h2 id="first-steps-title">
        Premiers pas
      </h2>
      <span data-test="first-steps-count">{{ doneCount }} sur {{ steps.length }}</span>
      <!-- Absent de la planche, gardé (règle 3) : masquer les premiers pas, « Annuler » pendant 6 secondes. -->
      <IconButton
        icon="close"
        label="Masquer les premiers pas"
        data-test="first-steps-dismiss"
        @click="emit('dismiss')"
      />
    </div>
    <ol class="fs-list">
      <li
        v-for="line in lines"
        :key="line.key"
        :class="{ 'fs-done': line.done, 'fs-locked': line.locked }"
        :aria-disabled="line.locked ? 'true' : undefined"
        :data-test="`first-step-${line.key}`"
      >
        <div class="fs-row">
          <span
            class="fs-mark"
            aria-hidden="true"
          ><AppIcon
            v-if="line.done"
            name="tick"
          /><template v-else>{{ line.n }}</template></span>
          <span class="fs-text">
            <b>{{ line.title }}</b>
            <span>{{ line.sub }}</span>
          </span>
          <b
            v-if="line.done"
            class="fs-ok"
          >Fait</b>
          <RouterLink
            v-else-if="line.current && !phone"
            :to="line.to"
            class="button-link primary-link fs-go"
            data-test="first-steps-action"
          >
            {{ line.action }}
          </RouterLink>
        </div>
        <RouterLink
          v-if="line.current && phone"
          :to="line.to"
          class="button-link primary-link fs-go"
          data-test="first-steps-action"
        >
          {{ line.action }}
        </RouterLink>
      </li>
    </ol>
  </section>
</template>

<style scoped>
/* Valeurs des planches avec les échelles ; hors échelle : la hauteur des lignes et le rond. */
.fs { --fs-row: 88px; --fs-mark: 36px; --fs-t: var(--font-title); --fs-s: var(--font-label); --fs-lh: var(--space-6); --fs-sl: 1.375rem; margin-top: var(--space-8); }
.fs-head { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-3); }
.fs-head h2 { flex: 1; margin: 0; font-size: var(--font-section); font-weight: var(--weight-heavy); }
.fs-head span { font-size: var(--font-label); color: var(--text-lead); }
.fs-head button { margin: calc(-1 * var(--space-3)); margin-left: 0; }
.fs-list { display: grid; gap: var(--space-3); margin: 0; padding: 0; list-style: none; }
.fs li { padding: 0 var(--space-5); border-radius: var(--space-5); background: var(--surface); }
.fs-row { display: flex; align-items: center; gap: var(--space-4); min-height: var(--fs-row); }
.fs-mark { flex: none; display: grid; place-items: center; width: var(--fs-mark); height: var(--fs-mark); border-radius: 50%; background: var(--action); color: var(--on-action); font-weight: var(--weight-bold); }
.fs-done .fs-mark { background: var(--success-soft); color: var(--success); }
.fs-mark :deep(svg) { width: 18px; height: 18px; stroke-width: 2.8; }
.fs-locked .fs-mark { background: var(--surface-muted); color: inherit; }
.fs-text { flex: 1; min-width: 0; }
.fs-text b { display: block; font-size: var(--fs-t); line-height: var(--fs-lh); }
.fs-text span, .fs-ok { font-size: var(--fs-s); }
.fs-text span, .fs-locked { color: var(--text-secondary); }
.fs-text span { display: block; margin-top: var(--space-1); line-height: var(--fs-sl); }
/* Grisées : sous-titre sur 20 px (24 px pour le titre au téléphone), comme sur les planches. */
.fs-locked { --fs-sl: var(--space-5); --fs-lh: var(--space-6); }
.fs-ok { color: var(--success); }
.fs-go { justify-content: center; height: var(--btn-tertiary); padding: 0 1.375rem; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); white-space: nowrap; }
/* Téléphone (AccueilNouveau) : la feuille blanche, des lignes de 72 px séparées par un trait. */
.fs-phone { --fs-row: 72px; --fs-mark: 2rem; --fs-t: var(--font-body); --fs-s: var(--font-small); --fs-lh: 1.375rem; --fs-sl: var(--space-5); padding: var(--space-6) var(--space-6) var(--space-2); border-radius: var(--space-8); background: var(--surface); }
.fs-phone h2 { font-size: var(--font-figure); }
.fs-phone .fs-list { gap: 0; }
.fs-phone li { padding: 0; border-radius: 0; }
.fs-phone li + li { border-top: 1px solid var(--line); }
.fs-phone .fs-go { display: flex; height: var(--btn-secondary); margin: var(--space-1) 0 var(--space-2); }
</style>
