<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import { dayMonthShort, meetingInLine, monthCaps, todayDay } from "../dates";
import { FEELINGS } from "../interviewLabels";

// « Faire le point » sur un entretien passé, en page entière (planches FairePoint et FairePointSombre du 18.11 ; accord
// de Kevin du 18.11.2026, 14 h 38). Trois réponses : le ressenti, la suite et les notes. La relance conseillée est
// calculée par le serveur (jour de l'entretien + 7 jours), jamais saisie. Aucune IA, le statut ne change pas.
type Debrief = { company: string; job_title: string; interview_at: string; feeling: string | null; next_step: string | null; notes: string | null; follow_up_on: string };
type Feeling = "bien" | "moyen" | "pas_bien";
type Next = "reponse" | "entretien" | "refus";

const route = useRoute();
const router = useRouter();
const id = computed(() => Number(route.params.id));
const debrief = ref<Debrief | null>(null);
const feeling = ref<Feeling | null>(null);
const next = ref<Next | null>(null);
const notes = ref("");
const busy = ref(false);
const error = ref("");

const NEXT: { key: Next; label: string }[] = [
  { key: "reponse", label: "J’attends une réponse" },
  { key: "entretien", label: "Un 2e entretien est prévu" },
  { key: "refus", label: "On m’a dit non" },
];
const day = computed(() => (debrief.value ? todayDay(new Date(debrief.value.interview_at)) : ""));
const caps = computed(() => (day.value ? monthCaps(Number(day.value.slice(5, 7))) : ""));
const dayNumber = computed(() => (day.value ? Number(day.value.slice(8, 10)) : 0));
// La pastille de la planche : seulement quand la personne attend une réponse.
const followUp = computed(() =>
  debrief.value && next.value === "reponse" ? `Relance conseillée le ${dayMonthShort(debrief.value.follow_up_on)} si rien d’ici là` : "",
);

function back(): void {
  if (router.options.history.state?.back) router.back();
  else void router.replace({ path: "/candidatures/suivi", query: { candidature: String(id.value) } });
}

onMounted(async () => {
  const { data } = await api.GET("/api/applications/{application_id}/debrief", { params: { path: { application_id: id.value } } });
  // Candidature supprimée ou sans entretien : Envoyées, sans erreur (comme le lien de la notification, Kevin 16.11).
  if (!data) {
    void router.replace({ path: "/candidatures/suivi" });
    return;
  }
  debrief.value = data;
  feeling.value = (data.feeling as Feeling | null) ?? null;
  next.value = (data.next_step as Next | null) ?? null;
  notes.value = data.notes ?? "";
});

async function save(): Promise<void> {
  if (!feeling.value) {
    error.value = "Dis comment ça s’est passé : bien, moyen ou pas bien.";
    document.querySelector<HTMLElement>("[data-test=feeling-bien]")?.focus();
    return;
  }
  busy.value = true;
  error.value = "";
  const { data } = await api.PUT("/api/applications/{application_id}/debrief", {
    params: { path: { application_id: id.value } },
    body: { feeling: feeling.value, next_step: next.value, notes: notes.value || null },
  });
  busy.value = false;
  if (!data) {
    error.value = "Point non enregistré. Réessaie dans un instant.";
    return;
  }
  back();
}
</script>

<template>
  <section
    class="faire-point"
    aria-labelledby="faire-point-title"
    data-test="faire-point"
  >
    <header class="faire-point-head">
      <button
        type="button"
        class="faire-point-back"
        aria-label="Retour"
        data-test="faire-point-back"
        @click="back"
      >
        <AppIcon name="arrow-left" />
      </button>
      <h1 id="faire-point-title">
        Faire le point
      </h1>
    </header>
    <template v-if="debrief">
      <div class="faire-point-body">
        <div
          class="faire-point-card faire-point-meeting"
          data-test="faire-point-meeting"
        >
          <span
            class="faire-point-date"
            aria-hidden="true"
          >
            <span>{{ caps }}</span>
            <b>{{ dayNumber }}</b>
          </span>
          <div>
            <p class="faire-point-title">
              Entretien · {{ debrief.job_title }}
            </p>
            <p class="faire-point-sub">
              {{ debrief.company }} · {{ meetingInLine(debrief.interview_at) }}
            </p>
          </div>
        </div>
        <h2 id="faire-point-feeling">
          Comment ça s’est passé ?
        </h2>
        <div class="faire-point-card faire-point-pad">
          <div
            class="faire-point-seg"
            role="radiogroup"
            aria-labelledby="faire-point-feeling"
          >
            <button
              v-for="(label, key) in FEELINGS"
              :key="key"
              type="button"
              role="radio"
              :aria-checked="feeling === key"
              :class="{ on: feeling === key }"
              :data-test="`feeling-${key}`"
              @click="feeling = key as Feeling"
            >
              {{ label }}
            </button>
          </div>
        </div>
        <h2 id="faire-point-next">
          La suite
        </h2>
        <div
          class="faire-point-card"
          role="radiogroup"
          aria-labelledby="faire-point-next"
        >
          <button
            v-for="item in NEXT"
            :key="item.key"
            type="button"
            role="radio"
            class="faire-point-row"
            :aria-checked="next === item.key"
            :data-test="`next-${item.key}`"
            @click="next = item.key"
          >
            <span :class="['faire-point-radio', { on: next === item.key }]" />
            <span>{{ item.label }}</span>
          </button>
        </div>
        <p
          v-if="followUp"
          class="faire-point-pill-line"
        >
          <span
            class="faire-point-pill"
            data-test="faire-point-follow-up"
          >{{ followUp }}</span>
        </p>
        <h2>Tes notes</h2>
        <div class="faire-point-card faire-point-pad">
          <label
            for="faire-point-notes"
            class="faire-point-label"
          >Ce qui a été dit, ce que tu veux retenir</label>
          <textarea
            id="faire-point-notes"
            v-model="notes"
            class="faire-point-notes"
            maxlength="2000"
            data-test="faire-point-notes"
          />
        </div>
        <p
          v-if="error"
          class="faire-point-error"
          role="alert"
          data-test="faire-point-error"
        >
          {{ error }}
        </p>
      </div>
      <div class="faire-point-foot">
        <button
          type="button"
          class="primary faire-point-save"
          :disabled="busy"
          data-test="faire-point-save"
          @click="save"
        >
          Enregistrer
        </button>
      </div>
    </template>
  </section>
</template>

<style>
/* Valeurs du HTML de la planche FairePoint (18.11) : en-tête de 52 (titre 22/800), cartes à 16 des bords (rayon 20,
   trait --line), titres de section 18/800 à 22 · 20 · 10, ressenti en trois boutons de 44 (rayon 22, 15/700), lignes de
   la suite de 56 avec un rond de 22, pastille grise 13/600 de 30, champ de notes de 96 (trait 1.5, rayon 14), barre du
   bas sur --surface avec un bouton plein de 52. */
.faire-point { --fp-2: 2px; --fp-5: 5px; --fp-13: 13px; --fp-10: 10px; --fp-14: 14px; --fp-15: 15px; --fp-18: 18px; --fp-19: 19px; --fp-20: 20px; --fp-22: 22px; --fp-28: 28px; --fp-30: 30px; --fp-32: 32px; --fp-44: 44px; --fp-46: 46px; --fp-50: 50px; --fp-52: 52px; --fp-56: 56px; --fp-96: 96px; min-height: 100dvh; display: flex; flex-direction: column; background: var(--bg); color: var(--text); }
.faire-point-head { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; min-height: var(--fp-52); padding: 0 var(--space-1); background: var(--bg); }
.faire-point-head h1 { margin: 0; font-size: var(--fp-22); font-weight: var(--weight-heavy); }
.faire-point-back { display: flex; align-items: center; justify-content: center; width: var(--fp-44); height: var(--fp-44); border: 0; background: transparent; color: var(--text); }
.faire-point-back .icon { width: var(--fp-22); height: var(--fp-22); }
.faire-point-body { flex: 1; padding-bottom: var(--space-6); }
.faire-point-body h2 { margin: var(--fp-22) var(--fp-20) var(--fp-10); font-size: var(--fp-18); font-weight: var(--weight-heavy); }
.faire-point-card { margin: 0 var(--space-4) var(--space-3); background: var(--surface); border: 1px solid var(--line); border-radius: var(--fp-20); overflow: hidden; }
.faire-point-pad { padding: var(--space-4); }
.faire-point-meeting { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); }
.faire-point-date { flex: none; display: flex; flex-direction: column; align-items: center; width: var(--fp-46); height: var(--fp-50); border-radius: var(--fp-10); box-shadow: inset 0 0 0 2px var(--primary-graphic); overflow: hidden; }
.faire-point-date span { width: 100%; background: var(--primary-graphic); color: var(--surface); font-size: var(--fp-10); font-weight: var(--weight-heavy); line-height: var(--space-4); text-align: center; }
.faire-point-date b { font-size: var(--fp-20); font-weight: var(--weight-heavy); line-height: var(--fp-32); color: var(--text); }
.faire-point-title { margin: 0; font-size: var(--fp-18); font-weight: var(--weight-bold); }
.faire-point-sub { margin: var(--fp-2) 0 0; font-size: var(--font-small); line-height: var(--fp-19); color: var(--text-secondary); }
.faire-point-seg { display: flex; gap: var(--space-2); }
.faire-point-seg button { flex: 1; height: var(--fp-44); border: 0; border-radius: var(--fp-22); background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--card-line); color: var(--text); font-size: var(--fp-15); font-weight: var(--weight-bold); }
.faire-point-seg button.on { background: var(--primary-soft); color: var(--primary-text); box-shadow: inset 0 0 0 2px var(--primary-graphic); }
.faire-point-row { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: var(--fp-56); padding: var(--fp-10) var(--space-4); border: 0; background: transparent; color: var(--text); font-size: var(--font-body); text-align: left; }
.faire-point-row + .faire-point-row { border-top: 1px solid var(--line-soft); }
.faire-point-radio { flex: none; width: var(--fp-22); height: var(--fp-22); border-radius: 50%; box-shadow: inset 0 0 0 2px var(--field-border); }
.faire-point-radio.on { box-shadow: inset 0 0 0 7px var(--primary-graphic); }
.faire-point-pill-line { margin: var(--space-3) var(--space-4) 0; }
.faire-point-pill { display: inline-flex; align-items: center; min-height: var(--fp-30); padding: var(--fp-5) var(--space-3); border-radius: var(--fp-15); background: var(--line-soft); color: var(--text-lead); font-size: var(--fp-13); font-weight: var(--weight-semibold); }
.faire-point-label { font-size: var(--fp-13); color: var(--text-secondary); }
.faire-point .faire-point-notes { display: block; box-sizing: border-box; width: 100%; min-height: var(--fp-96); margin-top: var(--space-2); padding: var(--space-3) var(--fp-14); border: 1.5px solid var(--field-border); border-radius: var(--fp-14); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body); line-height: var(--fp-22); resize: vertical; }
.faire-point-error { margin: var(--space-3) var(--fp-20) 0; font-size: var(--font-small); color: var(--danger); }
.faire-point-foot { position: sticky; bottom: 0; display: flex; padding: var(--space-3) var(--space-4) calc(var(--fp-28) + env(safe-area-inset-bottom)); background: var(--surface); border-top: 1px solid var(--line); }
.faire-point-save { flex: 1; justify-content: center; height: var(--fp-52); border-radius: var(--fp-28); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
