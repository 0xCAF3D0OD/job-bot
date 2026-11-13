<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";

import { api } from "../api/client";
import { AVAILABILITIES, NOTICES, PERMITS, groupThousands, isDay, linkedinProfile, parseSalary, shortAddress, type AnswerKey, type SalaryMode } from "../formAnswers";
import type { IconName } from "../icons";
import { usePhone } from "../composables/usePhone";
import { webAddress } from "../validators";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import BusyButton from "./BusyButton.vue";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import FormField from "./FormField.vue";

// Modifier une réponse pour les formulaires de candidature (récapitulatif du 11 novembre, PR 44 ; maquettes
// CoordonneesOrdinateur et CoordonneesTel, états li, perm, dispo, preav, sal) : le panneau de la PR 37, à droite sur
// ordinateur, feuille du bas sur téléphone. Une seule réponse à la fois ; le titre est une question, suivie d'une
// phrase qui explique le mot. « Enregistrer » enregistre cette réponse seule et ferme ; pas de bouton « Annuler ».
// Une ancienne saisie libre n'est jamais effacée sans un nouveau choix : le panneau la rappelle (« Tu avais écrit »).
const props = defineProps<{ field: AnswerKey | null; value: string; salaryMode: SalaryMode }>();
const emit = defineEmits<{ close: []; saved: [changes: Partial<Record<AnswerKey, string>> & { salary_mode?: SalaryMode }] }>();

// Sur téléphone, la feuille n'a que son titre (maquette CoordonneesTel).
const { phone } = usePhone();
const OTHER = "Autre";
const DATE = "Date précise";
const PANELS: Record<AnswerKey, { title: string; icon: IconName; lead: string; choices?: string[]; label?: string }> = {
  linkedin: { title: "Ton profil LinkedIn ?", icon: "linkedin", lead: "Copie l’adresse de ton profil depuis LinkedIn.", label: "Adresse du profil" },
  permit: { title: "Ton permis de travail ?", icon: "id-card", lead: "Ce que les employeurs demandent pour travailler en Suisse.", choices: [...PERMITS, OTHER], label: "Permis de travail" },
  availability: { title: "Quand peux-tu commencer ?", icon: "calendar", lead: "La date à partir de laquelle tu es libre.", choices: [...AVAILABILITIES, DATE], label: "Disponible dès" },
  notice: { title: "Ton délai de préavis ?", icon: "timer", lead: "Le temps à respecter avant de quitter ton poste actuel.", choices: [...NOTICES, OTHER], label: "Délai de préavis" },
  salary: { title: "Tes prétentions salariales ?", icon: "banknote", lead: "Le salaire annuel brut que tu demandes.", label: "Prétentions salariales (CHF brut par an)" },
  website: { title: "Ton site ou portfolio ?", icon: "globe", lead: "L’adresse de ton site, de ton portfolio ou de ton dépôt de code.", label: "Adresse du site" },
};
// Le titre garde l'espace fine insécable avant « ? ».
const panel = computed(() => (props.field ? PANELS[props.field] : null));
const title = computed(() => (panel.value?.title ?? "").replace(" ?", " ?"));

const text = ref("");
const choice = ref("");
const other = ref("");
const day = ref("");
const mode = ref<SalaryMode>("auto");
// L'ancienne saisie libre, quand elle ne correspond à aucun choix (ou à aucun montant lisible).
const before = ref("");
const touched = ref(false);
const error = ref("");
const message = ref("");
const busy = ref(false);
const picking = ref<"" | "date" | "time">("");
const body = ref<HTMLElement | null>(null);

watch(
  () => props.field,
  (field) => {
    text.value = "";
    choice.value = "";
    other.value = "";
    day.value = "";
    before.value = "";
    touched.value = false;
    error.value = "";
    message.value = "";
    picking.value = "";
    mode.value = props.salaryMode;
    if (!field) return;
    const value = props.value.trim();
    if (field === "linkedin" || field === "website") text.value = shortAddress(value);
    else if (field === "salary") {
      const amount = parseSalary(value);
      if (amount) text.value = groupThousands(amount);
      else before.value = value;
    } else if (field === "availability") {
      if (isDay(value)) {
        choice.value = DATE;
        day.value = value;
      } else if (AVAILABILITIES.includes(value)) choice.value = value;
      else before.value = value;
    } else if (value) {
      const known = (field === "permit" ? PERMITS : NOTICES).includes(value);
      choice.value = known ? value : OTHER;
      if (!known) other.value = value;
    }
  },
  { immediate: true },
);

// Un second appui retire le choix : la réponse peut redevenir vide.
function choose(option: string): void {
  touched.value = true;
  error.value = "";
  choice.value = choice.value === option ? "" : option;
  if (choice.value === OTHER) void nextTick(() => body.value?.querySelector<HTMLElement>("[data-test=answer-other]")?.focus());
}
// Les milliers se groupent pendant la saisie ; seuls les chiffres restent.
function onSalary(event: Event): void {
  const input = event.target as HTMLInputElement;
  text.value = groupThousands(input.value.replace(/\D/g, "").slice(0, 7));
  error.value = "";
}
function pickedDay(value: { date: string }): void {
  day.value = value.date;
  picking.value = "";
  touched.value = true;
  error.value = "";
  void nextTick(() => body.value?.querySelector<HTMLElement>("[data-test=dt-date]")?.focus());
}
function cancelPick(): void {
  picking.value = "";
  void nextTick(() => body.value?.querySelector<HTMLElement>("[data-test=dt-date]")?.focus());
}

// La valeur à enregistrer ; `undefined` : rien n'a été choisi, l'ancienne saisie reste.
function answer(): string | null | undefined {
  const field = props.field!;
  if (field === "linkedin") {
    const value = text.value.trim();
    if (value && !linkedinProfile(value)) error.value = "Une adresse de profil, par exemple linkedin.com/in/ton-nom.";
    return value || null;
  }
  if (field === "website") {
    error.value = webAddress(text.value) ?? "";
    return text.value.trim() || null;
  }
  if (field === "salary") {
    const digits = text.value.replace(/\D/g, "");
    if (!digits) return before.value ? undefined : null;
    if (!parseSalary(digits)) error.value = "Un montant annuel en francs, par exemple 95 000.";
    return digits;
  }
  if (before.value && !touched.value) return undefined;
  if (choice.value === OTHER) {
    if (!other.value.trim()) error.value = "Précise ta réponse, ou choisis-en une autre.";
    return other.value.trim();
  }
  if (choice.value === DATE) {
    if (!day.value) error.value = "Indique la date.";
    return day.value;
  }
  return choice.value || null;
}

async function save(): Promise<void> {
  const field = props.field;
  if (!field || busy.value) return;
  error.value = "";
  message.value = "";
  const value = answer();
  if (error.value) {
    await nextTick();
    body.value?.querySelector<HTMLElement>("[aria-invalid=true], input")?.focus();
    return;
  }
  const changes: Partial<Record<AnswerKey, string | null>> & { salary_mode?: SalaryMode } = {};
  if (value !== undefined) changes[field] = value;
  if (field === "salary") changes.salary_mode = mode.value;
  if (!Object.keys(changes).length) {
    emit("close");
    return;
  }
  busy.value = true;
  try {
    const { data } = await api.PUT("/api/identity", { body: changes });
    if (!data) {
      message.value = "Enregistrement refusé : vérifie ta réponse.";
      return;
    }
    const saved: Partial<Record<AnswerKey, string>> & { salary_mode?: SalaryMode } = {};
    if (value !== undefined) saved[field] = data[field] ?? "";
    if (field === "salary") saved.salary_mode = data.salary_mode ?? mode.value;
    emit("saved", saved);
    emit("close");
  } catch {
    message.value = "API injoignable.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="!!field"
    :title="title"
    :subtitle="phone ? '' : 'Pour les formulaires de candidature'"
    :icon="phone ? '' : panel?.icon ?? ''"
    class="answer-sheet"
    data-test="answer-sheet"
    @close="emit('close')"
  >
    <div
      v-if="field && panel"
      ref="body"
      class="answer-body"
    >
      <DateTimePanel
        v-if="picking"
        :date="day"
        time=""
        :with-time="false"
        title="Quand peux-tu commencer ?"
        @confirm="pickedDay"
        @cancel="cancelPick"
      />
      <form
        v-else
        id="answer-form"
        class="answer-form"
        novalidate
        data-test="answer-form"
        @submit.prevent="save"
      >
        <p class="answer-lead">
          {{ panel.lead }}
        </p>
        <p
          v-if="before"
          class="answer-before"
          data-test="answer-before"
        >
          Tu avais écrit : « {{ before }} »
        </p>

        <template v-if="panel.choices">
          <div
            class="answer-choices"
            role="radiogroup"
            :aria-label="panel.label"
          >
            <button
              v-for="option in panel.choices"
              :key="option"
              type="button"
              role="radio"
              :aria-checked="choice === option"
              :data-test="`answer-choice-${option}`"
              @click="choose(option)"
            >
              <AppIcon
                v-if="choice === option"
                name="tick"
              />{{ option }}
            </button>
          </div>
          <FormField
            v-if="choice === OTHER"
            v-slot="{ id, describedby, invalid }"
            label="Précise"
            :error="error"
          >
            <input
              :id="id"
              v-model="other"
              type="text"
              maxlength="200"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="answer-other"
              @input="touched = true; error = ''"
            >
          </FormField>
          <div
            v-else-if="choice === DATE"
            class="answer-date"
          >
            <DateTimeField
              :date="day"
              time=""
              :open="picking"
              :with-time="false"
              date-label="Date"
              compact
              outlined
              :aria-invalid="error ? 'true' : undefined"
              @open="picking = $event"
            />
            <p
              v-if="error"
              class="field-error"
              role="alert"
              data-test="field-error"
            >
              {{ error }}
            </p>
          </div>
          <p
            v-else-if="error"
            class="field-error"
            role="alert"
            data-test="field-error"
          >
            {{ error }}
          </p>
        </template>

        <template v-else>
          <FormField
            v-slot="{ id, describedby, invalid }"
            :label="panel.label!"
            :error="error"
          >
            <input
              v-if="field === 'salary'"
              :id="id"
              :value="text"
              type="text"
              inputmode="numeric"
              autocomplete="off"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="answer-input"
              @input="onSalary"
            >
            <input
              v-else
              :id="id"
              v-model="text"
              type="text"
              inputmode="url"
              autocapitalize="off"
              spellcheck="false"
              maxlength="300"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="answer-input"
              @input="error = ''"
            >
          </FormField>
          <template v-if="field === 'salary'">
            <p class="answer-private">
              <AppIcon name="lock" />Visible seulement par toi. Utilisé seulement si un formulaire le demande, jamais envoyé à l’IA.
            </p>
            <fieldset class="answer-mode">
              <legend>Si un formulaire le demande</legend>
              <label>
                <input
                  v-model="mode"
                  type="radio"
                  name="answer-salary-mode"
                  value="auto"
                  data-test="answer-mode-auto"
                >Le remplir automatiquement
              </label>
              <label>
                <input
                  v-model="mode"
                  type="radio"
                  name="answer-salary-mode"
                  value="demander"
                  data-test="answer-mode-demander"
                >Me demander avant
              </label>
            </fieldset>
          </template>
        </template>
        <p
          v-if="message"
          role="alert"
          class="notice error"
        >
          {{ message }}
        </p>
      </form>
    </div>
    <template
      v-if="!picking"
      #actions
    >
      <BusyButton
        type="submit"
        form="answer-form"
        class="primary action-1"
        :busy="busy"
        busy-label="Enregistrement…"
        data-test="answer-save"
      >
        Enregistrer
      </BusyButton>
    </template>
  </BottomSheet>
</template>

<style>
/* Maquette CoordonneesOrdinateur (états li, perm, dispo, preav, sal) : phrase 15/22 à 16 px du champ ; choix de 44 px
   à 8 px l'un de l'autre, le choisi en bordure de 2 px, fond teinté et coche ; note au cadenas 14/20 ; boutons radio
   de 20 px sur des lignes de 48 px ; bouton plein de 52 px sur toute la largeur. */
.answer-sheet { --as-52: 52px; --as-15: 0.9375rem; --as-22: 1.375rem; --as-dot: 20px; --as-ring: 6px; }
.answer-form { display: flex; flex-direction: column; gap: var(--space-4); }
.answer-form .form-field { margin: 0; min-width: 0; }
.answer-form input[type="text"] { width: 100%; min-width: 0; }
.answer-lead { margin: 0; font-size: var(--as-15); line-height: var(--as-22); color: var(--text-lead); }
.answer-before { margin: 0; padding: var(--space-3) var(--space-4); border-radius: var(--space-3); background: var(--surface-muted); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); overflow-wrap: anywhere; }
.answer-choices { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.answer-choices button {
  flex: none; display: flex; align-items: center; gap: var(--space-2); height: 2.75rem; padding: 0 var(--space-4);
  border: 1.5px solid var(--card-line); border-radius: var(--radius-pill); background: var(--surface); color: var(--text);
  font: inherit; font-size: var(--as-15); font-weight: var(--weight-semibold); cursor: pointer;
}
.answer-choices button[aria-checked="true"] { border: 2px solid var(--primary-graphic); background: var(--primary-soft); color: var(--primary-text); font-weight: var(--weight-bold); }
.answer-choices button svg { flex: none; width: var(--space-4); height: var(--space-4); }
.answer-date { display: grid; gap: var(--space-1); }
.answer-private { display: flex; gap: var(--space-2); margin: calc(-1 * var(--space-2)) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.answer-private svg { flex: none; width: var(--font-small); height: var(--font-small); margin-top: var(--space-1); }
.answer-mode { margin: var(--space-1) 0 0; padding: 0; border: 0; min-width: 0; }
.answer-mode legend { padding: 0; margin-bottom: var(--space-2); font-size: var(--as-15); font-weight: var(--weight-bold); }
.answer-mode label { display: flex; align-items: center; gap: var(--space-3); min-height: 3rem; font-size: var(--as-15); cursor: pointer; }
.answer-mode input { appearance: none; flex: none; width: var(--as-dot); height: var(--as-dot); margin: 0; box-sizing: border-box; border: 2px solid var(--field-border); border-radius: 50%; background: transparent; cursor: pointer; }
.answer-mode input:checked { border: var(--as-ring) solid var(--primary-graphic); }
.answer-mode input:focus-visible { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.answer-sheet :is(.sheet-actions) > .primary { width: 100%; min-height: var(--as-52); justify-content: center; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
