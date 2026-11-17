<script setup lang="ts">
import { computed, nextTick, ref } from "vue";

import AppIcon from "./AppIcon.vue";
import { BASE_LANGUAGES, LEVELS, languageLabel, type Level } from "./ProfileCompletionForm.vue";
import type { CriteriaSources } from "./WelcomeCriteria.vue";

// Premiers pas sur téléphone, une question par écran (§60 du LISEZMOI du 17.11, planches PremiersPas1Postes à
// PremiersPas6Langues et leurs versions sombres) : elles remplacent le formulaire long de l'étape 2. L'en-tête (retour,
// jobA1, « Passer ») et « Continuer » restent ceux de WelcomeView, qui tient la question affichée (`question`).
// Les données sont les mêmes qu'avant (postes, lieux, taux minimum, ORP, objectif, langues) ; WelcomeView les enregistre
// toutes après la question 6, comme le faisait l'étape 2. L'ordinateur garde WelcomeCriteria (OnboardingOrdinateurEtape2).
// Règles reprises : Lieu vide = « Toute la Suisse », jamais tiré du CV (§43) ; trois postes au plus.
const props = defineProps<{
  sources: CriteriaSources;
  reading: boolean;
  // Le CV envoyé n'a pas pu être lu : la pastille orange remplace « Depuis ton CV » (Kevin, 17.11, 15 h 07).
  cvUnread: boolean;
  maxRoles: number;
  cvLanguages: string[];
  savedLevels: Record<string, Level>;
}>();
const emit = defineEmits<{ edited: [key: keyof CriteriaSources] }>();
const question = defineModel<number>("question", { required: true });
const roles = defineModel<string[]>("roles", { required: true });
const picked = defineModel<string[]>("picked", { required: true });
const places = defineModel<string[]>("places", { required: true });
const rate = defineModel<number | null>("rate", { required: true });
const orp = defineModel<boolean>("orp", { required: true });
const target = defineModel<number>("target", { required: true });
const levels = defineModel<Record<string, Level> | null>("levels", { required: true });

const QUESTIONS: Record<number, { title: string; help: string }> = {
  1: { title: "Quels postes cherches-tu", help: "Choisis-en un ou plusieurs." },
  2: { title: "Où veux-tu travailler", help: "Laisse vide pour toute la Suisse." },
  3: { title: "À quel taux", help: "Le taux minimum que tu acceptes. Les offres au-dessus restent affichées." },
  4: { title: "Es-tu inscrit à l’ORP", help: "" },
  5: { title: "Combien de recherches par mois", help: "L’objectif fixé avec ton conseiller ORP." },
  6: { title: "Quelles langues parles-tu", help: "« Non renseigné » n’écarte aucune offre." },
};
const shown = computed(() => QUESTIONS[question.value] ?? QUESTIONS[1]!);

// 1. Postes : les postes proposés (CV ou saisis) en pastilles, cochées si choisies ; « + Autre poste » ouvre un champ.
const newRole = ref("");
const addingRole = ref(false);
const roleInput = ref<HTMLInputElement | null>(null);
function toggleRole(role: string): void {
  if (picked.value.includes(role)) picked.value = picked.value.filter((r) => r !== role);
  else if (picked.value.length < props.maxRoles) picked.value = [...picked.value, role];
  else return;
  emit("edited", "roles");
}
function openRole(): void {
  addingRole.value = true;
  void nextTick(() => roleInput.value?.focus());
}
function addRole(): void {
  const role = newRole.value.trim().slice(0, 80);
  newRole.value = "";
  if (!role) return;
  const same = roles.value.find((r) => r.toLowerCase() === role.toLowerCase());
  if (!same) roles.value = [...roles.value, role];
  const name = same ?? role;
  if (!picked.value.includes(name) && picked.value.length < props.maxRoles) picked.value = [...picked.value, name];
  emit("edited", "roles");
}

// 2. Lieu : une ville tapée devient une pastille cochée ; « Toute la Suisse » est cochée tant qu'il n'y en a aucune,
// et la toucher efface les villes.
const newPlace = ref("");
function addPlace(): void {
  const place = newPlace.value.trim().slice(0, 80);
  newPlace.value = "";
  if (!place || places.value.some((p) => p.toLowerCase() === place.toLowerCase())) return;
  places.value = [...places.value, place];
  emit("edited", "places");
}
function removePlace(place: string): void {
  places.value = places.value.filter((p) => p !== place);
  emit("edited", "places");
}
function wholeSwitzerland(): void {
  if (!places.value.length) return;
  places.value = [];
  emit("edited", "places");
}

// 3. Taux : un seul choix parmi les 7 valeurs déjà enregistrées, sans migration (Kevin, 17.11, 14 h 43, points 1 et
// 13) ; le minimum choisi part tel quel, « Tous » = peu importe.
const RATES = [
  { label: "Tous", min: null },
  ...[50, 60, 70, 80, 90].map((min) => ({ label: `Dès ${min}\u00A0%`, min })),
  { label: "100\u00A0%", min: 100 },
];
function chooseRate(min: number | null): void {
  if (rate.value === min) return;
  rate.value = min;
  emit("edited", "rate");
}

// 6. Langues : français, allemand, italien, anglais, puis celles déjà enregistrées ; celles du CV « Courant » au départ.
// Les langues renseignées d'abord, comme sur la planche. Toucher une ligne ouvre le choix du niveau du téléphone.
type Row = { name: string; level: Level; added: boolean; pos: number };
const start = levels.value ?? props.savedLevels;
const initial: Row[] = BASE_LANGUAGES.map((l, pos) => ({ name: l.name, level: start[l.name] ?? "unknown", added: false, pos }));
for (const [name, level] of Object.entries(start)) if (!initial.some((r) => r.name === name)) initial.push({ name, level, added: false, pos: initial.length });
for (const name of props.cvLanguages) {
  const row = initial.find((r) => r.name === name);
  if (row && row.level === "unknown") row.level = "fluent";
}
const rows = ref<Row[]>([...initial.filter((r) => r.level !== "unknown"), ...initial.filter((r) => r.level === "unknown")]);
const languagesFromCv = computed(() => props.cvLanguages.length > 0);
const levelLabel = (level: Level): string => LEVELS.find((l) => l.value === level)?.label ?? "";
function syncLevels(): void {
  // Enregistrées dans l'ordre habituel (français, allemand, italien, anglais, puis les autres), seul l'affichage change.
  const named = rows.value.filter((r) => r.name.trim()).sort((a, b) => a.pos - b.pos);
  levels.value = Object.fromEntries(named.map((r) => [r.name.trim().toLowerCase(), r.level]));
}
syncLevels();
function addLanguage(): void {
  rows.value = [...rows.value, { name: "", level: "unknown", added: true, pos: rows.value.length }];
}

function focusTitle(el: Element): void {
  el.querySelector<HTMLElement>("h1")?.focus({ preventScroll: true });
}

// « Continuer » : un poste ou une ville tapés sans valider comptent aussi.
defineExpose({
  flush: () => {
    if (newRole.value.trim()) addRole();
    if (newPlace.value.trim()) addPlace();
    syncLevels();
  },
});
</script>

<template>
  <div class="wq">
    <div
      class="wq-bar"
      role="progressbar"
      :aria-label="`Question ${question} sur 6`"
      aria-valuemin="1"
      aria-valuemax="6"
      :aria-valuenow="question"
    >
      <span
        v-for="i in 6"
        :key="i"
        :class="{ done: i <= question }"
      />
    </div>
    <Transition
      name="welcome-step"
      mode="out-in"
      @after-enter="focusTitle"
    >
      <div
        :key="question"
        class="wq-screen"
        :data-test="`question-${question}`"
      >
        <p
          class="wq-count"
          aria-hidden="true"
        >
          Question {{ question }} sur 6
        </p>
        <h1
          class="wq-title"
          tabindex="-1"
        >
          {{ `${shown.title} ?` }}
        </h1>
        <p
          v-if="shown.help"
          class="wq-help"
        >
          {{ shown.help }}
        </p>

        <template v-if="question === 1">
          <span
            v-if="sources.roles === 'cv'"
            class="wq-cv"
            data-test="question-cv"
          ><AppIcon name="tick" />Depuis ton CV</span>
          <span
            v-else-if="cvUnread"
            class="wq-cv wq-cv-unread"
            data-test="question-cv-unread"
          ><AppIcon name="alert-circle" />Ton CV n’a pas pu être lu</span>
          <p
            v-if="reading && !roles.length"
            class="wq-help"
          >
            Lecture du CV…
          </p>
          <div
            class="wq-chips"
            data-test="roles"
          >
            <button
              v-for="role in roles"
              :key="role"
              type="button"
              :class="['wq-chip', { on: picked.includes(role) }]"
              :aria-pressed="picked.includes(role)"
              :aria-disabled="!picked.includes(role) && picked.length >= maxRoles ? 'true' : undefined"
              @click="toggleRole(role)"
            >
              {{ role }}<svg
                v-if="picked.includes(role)"
                viewBox="0 0 24 24"
                aria-hidden="true"
              ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
            </button>
            <button
              v-if="!addingRole"
              type="button"
              class="wq-chip"
              data-test="role-other"
              @click="openRole"
            >
              + Autre poste
            </button>
          </div>
          <input
            v-if="addingRole"
            ref="roleInput"
            v-model="newRole"
            type="text"
            class="wq-field"
            maxlength="80"
            enterkeyhint="done"
            placeholder="Autre poste"
            aria-label="Autre poste"
            data-test="role-input"
            @keydown.enter.prevent="addRole"
            @blur="addRole"
          >
        </template>

        <template v-else-if="question === 2">
          <input
            v-model="newPlace"
            type="text"
            class="wq-field"
            maxlength="80"
            enterkeyhint="done"
            placeholder="Ville ou région"
            aria-label="Ville ou région"
            data-test="place-input"
            @keydown.enter.prevent="addPlace"
            @blur="addPlace"
          >
          <div class="wq-chips wq-places">
            <button
              v-for="place in places"
              :key="place"
              type="button"
              class="wq-chip on"
              aria-pressed="true"
              :aria-label="`Retirer ${place}`"
              @click="removePlace(place)"
            >
              {{ place }}<svg
                viewBox="0 0 24 24"
                aria-hidden="true"
              ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
            </button>
            <button
              type="button"
              :class="['wq-chip', { on: !places.length }]"
              :aria-pressed="!places.length"
              data-test="place-all"
              @click="wholeSwitzerland"
            >
              Toute la Suisse<svg
                v-if="!places.length"
                viewBox="0 0 24 24"
                aria-hidden="true"
              ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
            </button>
          </div>
        </template>

        <div
          v-else-if="question === 3"
          class="wq-chips"
          role="radiogroup"
          aria-label="Taux d’activité"
          data-test="rates"
        >
          <button
            v-for="choice in RATES"
            :key="choice.label"
            type="button"
            role="radio"
            :class="['wq-chip', { on: rate === choice.min }]"
            :aria-checked="rate === choice.min"
            @click="chooseRate(choice.min)"
          >
            {{ choice.label }}<svg
              v-if="rate === choice.min"
              viewBox="0 0 24 24"
              aria-hidden="true"
            ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
          </button>
        </div>

        <div
          v-else-if="question === 4"
          class="wq-cards"
          role="radiogroup"
          aria-label="Es-tu inscrit à l’ORP ?"
        >
          <button
            v-for="choice in [
              { value: true, label: 'Oui', sub: 'jobA1 compte tes recherches et prépare tes justificatifs' },
              { value: false, label: 'Non', sub: 'Tu pourras l’activer plus tard dans Réglages' },
            ]"
            :key="choice.label"
            type="button"
            role="radio"
            :class="['wq-card', { on: orp === choice.value }]"
            :aria-checked="orp === choice.value"
            :data-test="`orp-${choice.value ? 'yes' : 'no'}`"
            @click="orp = choice.value"
          >
            <span class="wq-card-text"><b>{{ choice.label }}</b><span>{{ choice.sub }}</span></span>
            <svg
              v-if="orp === choice.value"
              viewBox="0 0 24 24"
              aria-hidden="true"
            ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
          </button>
        </div>

        <div
          v-else-if="question === 5"
          class="wq-steps"
        >
          <button
            type="button"
            class="wq-stepper"
            aria-label="Une de moins"
            :disabled="target <= 1"
            data-test="target-minus"
            @click="target = Math.max(1, target - 1)"
          >
            −
          </button>
          <output
            class="wq-target"
            aria-live="polite"
            aria-label="Recherches par mois"
            data-test="target"
          >{{ target }}</output>
          <button
            type="button"
            class="wq-stepper"
            aria-label="Une de plus"
            :disabled="target >= 99"
            data-test="target-plus"
            @click="target = Math.min(99, target + 1)"
          >
            +
          </button>
        </div>

        <template v-else>
          <span
            v-if="languagesFromCv"
            class="wq-cv wq-cv-langs"
          ><AppIcon name="tick" />Depuis ton CV</span>
          <div
            class="wq-langs"
            data-test="languages"
          >
            <div
              v-for="(row, index) in rows"
              :key="index"
              class="wq-lang"
            >
              <input
                v-if="row.added"
                v-model="row.name"
                type="text"
                maxlength="40"
                class="wq-lang-name"
                placeholder="Espagnol"
                aria-label="Langue"
                @change="syncLevels"
              >
              <b v-else>{{ languageLabel(row.name) }}</b>
              <span :class="['wq-level', { unset: row.level === 'unknown' }]">
                {{ levelLabel(row.level) }}<svg
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                ><path d="m9 6 6 6-6 6" /></svg>
                <select
                  v-model="row.level"
                  :aria-label="`Niveau en ${row.added ? row.name || 'cette langue' : languageLabel(row.name).toLowerCase()}`"
                  :data-test="`level-${row.name || index}`"
                  @change="syncLevels"
                >
                  <option
                    v-for="level in LEVELS"
                    :key="level.value"
                    :value="level.value"
                  >
                    {{ level.label }}
                  </option>
                </select>
              </span>
            </div>
          </div>
          <button
            type="button"
            class="wq-add"
            data-test="language-add"
            @click="addLanguage"
          >
            + Ajouter une langue
          </button>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style>
/* §60 du 17.11 (planches PremiersPas…) : la colonne des premiers pas a 20 px de marge, la planche 24 : 4 px de plus ici. */
.wq {
  --wq-2: 2px; --wq-3: 3px; --wq-6: 6px; --wq-10: 10px; --wq-13: 13px; --wq-14: 14px; --wq-15: 15px; --wq-16: 16px; --wq-17: 17px; --wq-18: 18px; --wq-20: 20px; --wq-22: 22px; --wq-26: 26px; --wq-32: 32px; --wq-48: 48px;
  display: flex; flex-direction: column; flex: 1; padding: 0 var(--space-1); }
.wq-bar { display: flex; gap: var(--wq-6); padding-top: var(--wq-6); }
.wq-bar span { flex: 1; height: 5px; border-radius: var(--wq-3); background: var(--line); transition: background-color 0.4s; }
.wq-bar span.done { background: var(--primary-graphic); }
.wq-screen { display: flex; flex-direction: column; }
.wq-count { margin: var(--wq-14) 0 0; font-size: var(--wq-13); font-weight: var(--weight-bold); color: var(--text-secondary); }
.wq-title { margin: var(--space-2) 0 var(--wq-6); font-size: var(--wq-26); line-height: var(--wq-32); font-weight: var(--weight-heavy); }
.wq-title:focus { outline: none; }
.wq-help { margin: 0 0 var(--wq-18); font-size: var(--wq-15); line-height: var(--wq-22); color: var(--text-secondary); }
.wq-title + :not(.wq-help) { margin-top: var(--wq-14); }
.wq-cv { align-self: flex-start; display: inline-flex; align-items: center; gap: var(--wq-6); height: 28px; margin-bottom: var(--space-3); padding: 0 var(--wq-10); border-radius: var(--wq-14); background: var(--success-soft); color: var(--success); font-size: var(--wq-13); font-weight: var(--weight-bold); }
.wq-cv-unread { background: var(--warning-soft); color: var(--warning); }
.wq-cv .icon { width: var(--wq-14); height: var(--wq-14); }
.wq-cv-langs { margin-bottom: var(--wq-10); }
.wq-chips { display: flex; flex-wrap: wrap; gap: var(--wq-10); }
.wq-chip { display: inline-flex; align-items: center; gap: var(--space-2); min-height: 51px; padding: 0 var(--space-4); border-radius: var(--wq-14); background: var(--surface); border: 1.5px solid var(--line); color: var(--text); font-size: var(--font-body); font-weight: var(--weight-semibold); cursor: pointer; }
.wq-chip.on { background: var(--primary-soft); border-color: var(--primary-graphic); color: var(--primary-text); }
.wq-chip svg, .wq-card svg { flex: none; width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; }
.wq input.wq-field { box-sizing: border-box; width: 100%; height: 59px; margin-top: var(--wq-14); padding: 0 var(--space-4); border-radius: var(--wq-16); background: var(--surface); border: 1.5px solid var(--card-line); color: var(--text); font-size: var(--font-body); }
.wq input.wq-field::placeholder { color: var(--text-secondary); opacity: 1; }
.wq-chips + input.wq-field { margin-top: var(--space-3); }
.wq-places { margin-top: var(--wq-14); }
.wq-title + input.wq-field { margin-top: 0; }
.wq-help + input.wq-field { margin-top: 0; }
.wq-cards { display: flex; flex-direction: column; gap: var(--space-3); }
.wq-card { display: flex; align-items: center; line-height: normal; gap: var(--space-3); padding: var(--space-4) var(--wq-18); border-radius: var(--wq-18); background: var(--surface); border: 1.5px solid var(--line); color: var(--text); text-align: left; white-space: normal; cursor: pointer; }
.wq-card.on { background: var(--primary-soft); border-color: var(--primary-graphic); color: var(--primary-text); }
.wq-card-text { flex: 1; }
.wq-card-text b { display: block; font-size: var(--wq-17); }
.wq-card-text span { display: block; margin-top: var(--wq-2); font-size: var(--font-small); line-height: var(--wq-20); font-weight: var(--weight-regular); color: var(--text-secondary); }
.wq-steps { display: flex; align-items: center; justify-content: center; gap: var(--space-6); margin-top: var(--space-2); }
.wq-stepper { display: grid; place-items: center; width: 59px; height: 59px; padding: 0; border-radius: 50%; border: 1.5px solid var(--button-outline); background: var(--surface); color: var(--text); font-size: var(--wq-26); font-weight: var(--weight-regular); }
.wq-target { min-width: 70px; text-align: center; font-size: var(--wq-48); font-weight: var(--weight-heavy); }
.wq-langs { background: var(--surface); border: 1.5px solid var(--line); border-radius: var(--wq-18); overflow: hidden; }
.wq-lang { display: flex; align-items: center; gap: var(--space-3); min-height: 60px; padding: 0 var(--space-4); }
.wq-lang + .wq-lang { border-top: 1px solid var(--surface-muted); }
.wq-lang b { flex: 1; font-size: var(--font-body); }
.wq-lang:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: -2px; }
.wq input.wq-lang-name { flex: 1; min-width: 0; height: 40px; padding: 0; border: 0; background: transparent; color: var(--text); font-size: var(--font-body); font-weight: var(--weight-bold); }
.wq-level { position: relative; display: flex; align-items: center; gap: var(--wq-6); min-height: 60px; font-size: var(--wq-15); color: var(--text); }
.wq-level.unset { color: var(--unrated-dash); }
.wq-level svg { width: 18px; height: 18px; fill: none; stroke: var(--field-border); stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }
/* Le choix du niveau du téléphone, invisible, posé sur le niveau et son chevron. */
.wq-level select { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.wq-add { align-self: flex-start; min-height: var(--target-min); margin-top: var(--space-1); padding: 0; background: none; border: 0; font-size: var(--wq-15); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer; }
/* L'écran et « Continuer » de WelcomeView pendant les questions : foncé, le guillemet de 22 px à droite. Ces règles
   viennent avec ce fichier, chargé seulement sur téléphone. */
.welcome-questions { gap: 0; padding-top: 0; }
.welcome-cta.welcome-ink { --welcome-ink-size: 17px; padding: 0 var(--space-6); border: 0; background: var(--text); color: var(--bg); font-size: var(--welcome-ink-size); cursor: pointer; }
.welcome-guillemet { font-size: var(--title-sub); }
@media (prefers-reduced-motion: reduce) { .wq-bar span { transition: none; } }
</style>
