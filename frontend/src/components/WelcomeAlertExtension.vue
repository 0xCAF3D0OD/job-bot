<script setup lang="ts">
import { computed, ref } from "vue";

import type { AlertStep } from "../composables/useJobA1Extension";
import AppIcon from "./AppIcon.vue";

// Premiers pas, « Crée ton alerte sur jobup », avec l'extension (section 42 du paquet du 16.11 ; planches
// OnboardingOrdinateurAlerteExtInstaller, …Ext et …ExtSuivi, ordinateur seulement). Même carte que le parcours à la
// main (WelcomeAlertSteps, classes wa-*).
// - Extension absente : 3 étapes, la première mène à la boutique.
// - Extension installée : 2 étapes ; pendant la création, le suivi en direct que l'extension envoie à la page (l'étape
//   seulement, jamais le code). Pas de bouton « J'ai créé l'alerte » : la vue passe à la suite à « created ».
const props = defineProps<{ searchLabel: string; url: string | null; installed: boolean; progress: AlertStep | null }>();

// La fiche de la boutique (la même que Réglages › Extension, docs/71 §8).
const STORE_URL = "https://addons.mozilla.org/addon/joba1-remplir-mes-candidatures/";

const opened = ref(false);
const started = computed(() => opened.value || !!props.progress);
const RANK: Record<AlertStep, number> = { filled: 1, sent: 2, "code-pasted": 3, fallback: 3, created: 4 };
const rank = computed(() => (props.progress ? RANK[props.progress] : 0));

type Mark = "done" | "now" | "next";
const marks = computed<Mark[]>(() => {
  if (!props.installed) return ["now", "next", "next"];
  return started.value ? ["done", "now"] : ["now", "next"];
});

// Le suivi : fait, en cours (la roue) ou à venir.
const TRACK = ["Formulaire rempli", "Alerte envoyée à jobup", "Code collé dans jobup", "En attente de ta confirmation sur jobup"];
const track = computed(() =>
  TRACK.map((label, i) => ({
    label: i === 2 && props.progress === "fallback" ? "Le code est dans la fenêtre de l’extension" : label,
    mark: (i < rank.value ? "done" : i === rank.value ? "now" : "next") as Mark,
  })),
);
</script>

<template>
  <ol
    class="wa wa-desk"
    data-test="welcome-alert-extension"
  >
    <li
      v-for="(mark, i) in marks"
      :key="`${installed}-${i}`"
      :class="['wa-step', mark]"
      :aria-current="mark === 'now' ? 'step' : undefined"
      :data-test="`welcome-ext-step-${i + 1}`"
    >
      <span
        class="wa-num"
        aria-hidden="true"
      ><AppIcon
        v-if="mark === 'done'"
        name="tick"
      /><template v-else>{{ i + 1 }}</template></span>
      <span class="visually-hidden">{{ mark === "done" ? "Fait : " : mark === "now" ? "En cours : " : "" }}</span>
      <div class="wa-body">
        <template v-if="!installed && i === 0">
          <b class="wa-title">Installe l’extension jobA1</b>
          <span class="wa-help">Gratuite, pour Firefox. Elle n’agit que sur les pages d’alerte que tu ouvres.</span>
          <div class="wa-open-row">
            <a
              :href="STORE_URL"
              target="_blank"
              rel="noopener noreferrer"
              class="button-link primary-link wa-open"
              data-test="welcome-ext-install"
            >Installer l’extension<span class="visually-hidden"> (nouvel onglet)</span></a>
          </div>
        </template>

        <template v-else-if="(installed && i === 0) || (!installed && i === 1)">
          <b class="wa-title">Ouvre jobup</b>
          <span class="wa-help">{{ mark === "done" ? `Recherche : ${searchLabel}.` : "L’extension remplit le formulaire avec ta recherche et ton adresse jobA1." }}</span>
          <div
            v-if="installed && mark === 'now' && url"
            class="wa-open-row"
          >
            <a
              :href="url"
              target="_blank"
              rel="noopener noreferrer"
              class="button-link primary-link wa-open"
              data-test="welcome-ext-open"
              @click="opened = true"
            ><AppIcon name="external" />Ouvrir jobup avec ma recherche<span class="visually-hidden"> (nouvel onglet)</span></a>
          </div>
          <a
            v-else-if="installed && mark === 'done' && url"
            :href="url"
            target="_blank"
            rel="noopener noreferrer"
            class="wa-link"
            data-test="welcome-ext-reopen"
          >Rouvrir jobup<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </template>

        <template v-else>
          <b class="wa-title">Crée l’alerte, puis confirme le code</b>
          <span class="wa-help">L’extension colle le code pour toi. C’est toi qui cliques sur jobup.<template v-if="installed"> Cette page passe à la suite dès que l’alerte est créée.</template></span>
          <ul
            v-if="installed && started"
            class="wa-follow"
            role="status"
            data-test="welcome-ext-track"
          >
            <li
              v-for="item in track"
              :key="item.label"
              :class="item.mark"
            >
              <AppIcon
                v-if="item.mark === 'done'"
                name="tick"
              /><svg
                v-else-if="item.mark === 'now'"
                class="wa-spinner"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                aria-hidden="true"
              ><circle
                class="wa-track"
                cx="12"
                cy="12"
                r="9"
                fill="none"
                stroke-width="3"
              /><path
                class="wa-arc"
                d="M12 3a9 9 0 0 1 9 9"
                fill="none"
                stroke-width="3"
                stroke-linecap="round"
              /></svg><span
                v-else
                class="wa-dot"
                aria-hidden="true"
              /><span><span class="visually-hidden">{{ item.mark === "done" ? "Fait : " : item.mark === "now" ? "En cours : " : "À venir : " }}</span>{{ item.label }}</span>
            </li>
          </ul>
        </template>
      </div>
    </li>
  </ol>
</template>

<style>
/* Le suivi en direct (planche OnboardingOrdinateurAlerteExtSuivi) : coches vertes, la ligne en cours en gras avec la
   roue, les suivantes en gris. */
.wa-follow { --wa-follow-gap: 4px; --wa-follow-icon: 16px; display: grid; gap: var(--wa-follow-gap); margin: var(--space-3) 0 0; padding: 0; list-style: none; font-size: var(--wa-help); line-height: var(--wa-help-lh); color: var(--text-lead); }
.wa-follow > li { display: flex; align-items: center; gap: var(--wa-8); }
.wa-follow > li .icon { flex: none; width: var(--wa-follow-icon); height: var(--wa-follow-icon); color: var(--success); stroke-width: 2.4; }
.wa-follow > li.now { font-weight: var(--weight-bold); color: var(--text); }
.wa-follow > li.next { color: var(--text-secondary); }
.wa-follow .wa-spinner { margin-top: 0; }
.wa-dot { flex: none; width: var(--wa-follow-icon); height: var(--wa-follow-icon); border: 2px solid var(--line); border-radius: var(--radius-pill); box-sizing: border-box; }
</style>
