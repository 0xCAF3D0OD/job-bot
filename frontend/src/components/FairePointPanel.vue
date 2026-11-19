<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import { dayMonthShort, meetingInLine } from "../dates";
import { FEELINGS } from "../interviewLabels";
import CalendarDate from "./CalendarDate.vue";

// « Faire le point » sur ordinateur, dans le panneau de droite de Rendez-vous (planches FairePointOrdinateur et
// FairePointOrdinateurSombre, §72m et §72n du 19.11 ; accord de Kevin du 19.11.2026). Les trois réponses du téléphone :
// le ressenti, la suite et les notes. Un entretien « À noter » enregistre le point du jour prévu ; un retour de
// « Passés » (ou « Voir le retour ») se rouvre prérempli et se met à jour. La relance est calculée par le serveur.
type Debrief = { company: string; job_title: string; interview_at: string; feeling: string | null; next_step: string | null; notes: string | null; follow_up_on: string };
type Feeling = "bien" | "moyen" | "pas_bien";
type Next = "reponse" | "entretien" | "refus";

const props = defineProps<{
  // Le point du jour prévu d'une candidature, ou un retour déjà fait.
  source: { kind: "application"; id: number } | { kind: "interview"; id: number };
  // L'heure n'est connue que pour l'entretien prévu.
  withTime: boolean;
  done: boolean;
}>();
const emit = defineEmits<{ saved: [] }>();

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
const at = computed(() => (debrief.value ? new Date(debrief.value.interview_at) : null));
// « Entretien · DevOps Engineer · Alpstack, mercredi 12 nov., 14 h ».
const line = computed(() => {
  const d = debrief.value;
  if (!d) return "";
  const when = meetingInLine(d.interview_at);
  return `Entretien · ${d.job_title || "Poste non indiqué"} · ${d.company}, ${props.withTime ? when : when.replace(/, [^,]*$/, "")}`;
});
const followUp = computed(() =>
  debrief.value && next.value === "reponse" ? `Relance conseillée le ${dayMonthShort(debrief.value.follow_up_on)} si rien d’ici là` : "",
);

async function load(): Promise<Debrief | undefined> {
  const id = props.source.id;
  return props.source.kind === "application"
    ? (await api.GET("/api/applications/{application_id}/debrief", { params: { path: { application_id: id } } })).data
    : (await api.GET("/api/interviews/{interview_id}/debrief", { params: { path: { interview_id: id } } })).data;
}

async function store(body: { feeling: Feeling; next_step: Next | null; notes: string | null }): Promise<boolean> {
  const id = props.source.id;
  const { data } =
    props.source.kind === "application"
      ? await api.PUT("/api/applications/{application_id}/debrief", { params: { path: { application_id: id } }, body })
      : await api.PUT("/api/interviews/{interview_id}/debrief", { params: { path: { interview_id: id } }, body });
  return !!data;
}

onMounted(async () => {
  const data = await load();
  if (!data) {
    error.value = "Ce point n’a pas pu être ouvert. Réessaie dans un instant.";
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
    document.querySelector<HTMLElement>("[data-test=fpo-feeling-bien]")?.focus();
    return;
  }
  busy.value = true;
  error.value = "";
  const ok = await store({ feeling: feeling.value, next_step: next.value, notes: notes.value || null });
  busy.value = false;
  if (!ok) {
    error.value = "Point non enregistré. Réessaie dans un instant.";
    return;
  }
  emit("saved");
}
</script>

<template>
  <article
    class="rdv-open fpo"
    aria-labelledby="fpo-title"
    data-test="rdv-detail-point"
  >
    <template v-if="debrief && at">
      <div class="rdv-open-head">
        <CalendarDate
          :day="at.getDate()"
          :month="at.getMonth() + 1"
          :tone="done ? 'past' : 'orp'"
          :size="56"
        />
        <div class="rdv-open-head-text">
          <h2 id="fpo-title">
            Faire le point
          </h2>
          <p data-test="fpo-line">
            {{ line }}
          </p>
        </div>
      </div>
      <section aria-labelledby="fpo-feeling">
        <h3
          id="fpo-feeling"
          class="rdv-open-title"
        >
          Comment ça s’est passé ?
        </h3>
        <div
          class="fpo-seg"
          role="radiogroup"
          aria-labelledby="fpo-feeling"
        >
          <button
            v-for="(label, key) in FEELINGS"
            :key="key"
            type="button"
            role="radio"
            :aria-checked="feeling === key"
            :class="{ on: feeling === key }"
            :data-test="`fpo-feeling-${key}`"
            @click="feeling = key as Feeling"
          >
            {{ label }}
          </button>
        </div>
      </section>
      <section aria-labelledby="fpo-next">
        <h3
          id="fpo-next"
          class="rdv-open-title"
        >
          La suite
        </h3>
        <div
          class="fpo-card"
          role="radiogroup"
          aria-labelledby="fpo-next"
        >
          <button
            v-for="item in NEXT"
            :key="item.key"
            type="button"
            role="radio"
            class="fpo-row"
            :aria-checked="next === item.key"
            :data-test="`fpo-next-${item.key}`"
            @click="next = item.key"
          >
            <span :class="['fpo-radio', { on: next === item.key }]" />
            <span>{{ item.label }}</span>
          </button>
        </div>
        <span
          v-if="followUp"
          class="fpo-pill"
          data-test="fpo-follow-up"
        >{{ followUp }}</span>
      </section>
      <section aria-labelledby="fpo-notes-title">
        <h3
          id="fpo-notes-title"
          class="rdv-open-title"
        >
          Tes notes
        </h3>
        <label
          for="fpo-notes"
          class="fpo-label"
        >Ce qui a été dit, ce que tu veux retenir</label>
        <textarea
          id="fpo-notes"
          v-model="notes"
          class="fpo-notes"
          rows="3"
          maxlength="2000"
          data-test="fpo-notes"
        />
      </section>
      <p
        v-if="error"
        class="fpo-error"
        role="alert"
        data-test="fpo-error"
      >
        {{ error }}
      </p>
      <div class="fpo-foot">
        <button
          type="button"
          class="primary fpo-save"
          :disabled="busy"
          data-test="fpo-save"
          @click="save"
        >
          Enregistrer
        </button>
      </div>
    </template>
    <p
      v-else-if="error"
      class="fpo-error"
      role="alert"
    >
      {{ error }}
    </p>
  </article>
</template>

<style>
/* Valeurs du HTML de la planche FairePointOrdinateur (§72m, §72n du 19.11), dans le cadre de Rendez-vous ouvert
   (.rdv-open : 680 au plus, 24 entre les blocs, tuile date de 56, titre 24/30/800, titres de bloc 18/24/800). Ressenti :
   trois boutons de 48 (coins de 24, 16/700, écart 10) posés sur le fond, sans carte. La suite : une carte blanche au
   trait 1,5 (--card-line), coins de 18, lignes de 56 (marges 18, écart 14) avec un rond de 22, séparées par un trait.
   Pastille grise 13/600 (5/12, coins de 15) à 10 sous la carte. Notes sans carte : libellé 13 gris à 8 au-dessus d'un
   champ au trait 1,5 (coins de 12, 12/14, 16/24). « Enregistrer » plein de 48 (0 28, coins de 24), à gauche. */
.fpo { --fpo-4: 4px; --fpo-5: 5px; --fpo-10: 10px; --fpo-13: 13px; --fpo-14: 14px; --fpo-15: 15px; --fpo-18: 18px; --fpo-22: 22px; --fpo-24: 24px; --fpo-28: 28px; --fpo-48: 48px; --fpo-56: 56px; --fpo-99: 99px; }
.fpo section > .rdv-open-title { margin-bottom: var(--fpo-10); }
.fpo-seg { display: flex; gap: var(--fpo-10); }
.fpo .fpo-seg button {
  flex: 1; display: flex; align-items: center; justify-content: center; height: var(--fpo-48); min-height: var(--fpo-48); padding: 0; border: 0; border-radius: var(--fpo-24);
  background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--card-line); color: var(--text); font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold);
}
.fpo .fpo-seg button.on { background: var(--primary-soft); color: var(--primary-text); box-shadow: inset 0 0 0 2px var(--primary-graphic); }
.fpo-card { background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--fpo-18); overflow: hidden; }
.fpo .fpo-row {
  display: flex; align-items: center; gap: var(--fpo-14); box-sizing: border-box; width: 100%; min-height: var(--fpo-56); padding: 0 var(--fpo-18); border: 0; border-radius: 0;
  background: transparent; box-shadow: none; color: var(--text); font: inherit; font-size: var(--font-body); font-weight: var(--weight-regular); text-align: left; cursor: pointer;
}
.fpo .fpo-row + .fpo-row { border-top: 1px solid var(--line); }
.fpo-radio { flex: none; box-sizing: border-box; width: var(--fpo-22); height: var(--fpo-22); border-radius: 50%; border: 2px solid var(--field-border); }
.fpo-radio.on { border-color: var(--primary-graphic); box-shadow: inset 0 0 0 4px var(--surface), inset 0 0 0 9px var(--primary-graphic); }
.fpo-pill {
  display: inline-flex; margin: var(--fpo-10) 0 0 var(--fpo-4); padding: var(--fpo-5) var(--space-3); border-radius: var(--fpo-15);
  background: var(--line-soft); color: var(--text-lead); font-size: var(--fpo-13); font-weight: var(--weight-semibold);
}
.fpo-label { display: block; margin: 0 0 var(--space-2) var(--fpo-4); font-size: var(--fpo-13); color: var(--text-secondary); }
.fpo .fpo-notes {
  display: block; box-sizing: border-box; width: 100%; min-height: var(--fpo-99); padding: var(--space-3) var(--fpo-14); border: 1.5px solid var(--field-border); border-radius: var(--space-3);
  background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body); line-height: var(--fpo-24); resize: vertical;
}
.fpo-error { margin: 0; font-size: var(--font-small); color: var(--danger); }
.fpo-foot { display: flex; }
.fpo .fpo-save { height: var(--fpo-48); min-height: var(--fpo-48); padding: 0 var(--fpo-28); border-radius: var(--fpo-24); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
