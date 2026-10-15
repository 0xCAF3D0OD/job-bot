<script setup lang="ts">
import { reactive, ref } from "vue";

import { api, type Training } from "../api/client";
import { highlight, languageLabel } from "../newsLabels";
import HelpTip from "./HelpTip.vue";
import { FORMATS, KINDS, LEVELS, PRICES, STATUSES } from "../trainingLabels";

// Contenu d'une formation (docs/16 §5) : la carte du catalogue sur ordinateur, la fiche en
// plein écran sur téléphone (docs/34 §2).
export type TrainingStatus = "interested" | "in_progress" | "done";
export type MarkExtra = { progress?: string | null; done_at?: string | null; certified?: boolean | null };
type Status = TrainingStatus;

const props = defineProps<{ training: Training }>();
const emit = defineEmits<{
  mark: [status: Status | null, extra?: MarkExtra];
  review: [keep: boolean];
  // Bloc de profil créé (docs/37 §1) : le suivi renvoyé, avec le lien vers le bloc.
  linked: [mark: NonNullable<Training["mark"]>];
}>();

// Une formation terminée entre dans Mon parcours (docs/37 §1) : un bloc « formation »
// prérempli, relu avant l'enregistrement. Pas d'IA, rien n'est renoté d'office.
const drafting = ref(false);
const saving = ref(false);
const error = ref("");
const block = reactive({ title: "", content: "", tags: "" });
const monthYear = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric" });

function startDraft(): void {
  const t = props.training;
  const done = t.mark?.done_at ? new Date(`${t.mark.done_at}T12:00:00`) : new Date();
  const facts = `Formation terminée en ${monthYear.format(done)}${t.mark?.certified ? ", certificat obtenu" : ""}.`;
  block.title = `${t.title} (${t.provider})`;
  block.content = [facts, t.description].filter(Boolean).join(" ");
  block.tags = t.tags.join(", ");
  error.value = "";
  drafting.value = true;
}

async function save(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const { data, error: failure } = await api.POST("/api/trainings/{training_id}/profile-block", {
      params: { path: { training_id: props.training.id } },
      body: {
        title: block.title,
        content: block.content,
        tags: block.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      },
    });
    if (!data) {
      const detail = (failure as { detail?: unknown } | undefined)?.detail;
      error.value = typeof detail === "string" ? `Ajout impossible : ${detail}.` : "Ajout impossible : vérifie le titre et le texte.";
      return;
    }
    drafting.value = false;
    emit("linked", data);
  } finally {
    saving.value = false;
  }
}

const inputValue = (event: Event): string => (event.target as HTMLInputElement).value;
</script>

<template>
  <div class="training-head">
    <span class="news-meta">{{ KINDS[training.kind] }} · {{ training.provider }}</span>
    <span
      v-if="!training.verified"
      class="badge warn"
      data-test="unverified"
    >à vérifier</span>
  </div>
  <a
    class="training-title"
    :href="training.url"
    target="_blank"
    rel="noopener noreferrer"
  ><template
    v-for="(part, index) in highlight(training.title, training.matched)"
    :key="index"
  ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></a>
  <p class="training-facts">
    {{ FORMATS[training.format] }} · {{ languageLabel(training.language) }} · {{ PRICES[training.price] }}
    <template v-if="training.level">
      · {{ LEVELS[training.level] }}
    </template>
    <template v-if="training.duration">
      · {{ training.duration }}
    </template>
  </p>
  <p
    v-if="training.description"
    class="training-text"
  >
    {{ training.description }}
  </p>
  <p
    v-if="training.prep"
    class="training-text"
  >
    <strong>Préparation conseillée :</strong> {{ training.prep }}
  </p>
  <p
    v-if="training.price === 'paid'"
    class="hint"
  >
    Financement possible seulement avec l'accord préalable de ton conseiller ORP.
  </p>
  <div
    v-if="!training.verified"
    class="training-actions"
  >
    <button
      type="button"
      class="secondary small"
      data-test="keep"
      @click="emit('review', true)"
    >
      Garder
    </button>
    <button
      type="button"
      class="link danger"
      data-test="dismiss"
      @click="emit('review', false)"
    >
      Écarter
    </button>
  </div>
  <div class="training-actions">
    <div
      class="segmented"
      role="radiogroup"
      aria-label="Suivi"
    >
      <button
        v-for="(label, key) in STATUSES"
        :key="key"
        type="button"
        role="radio"
        :aria-checked="training.mark?.status === key"
        :data-test="`mark-${key}`"
        @click="emit('mark', training.mark?.status === key ? null : (key as Status))"
      >
        {{ label }}
      </button>
    </div>
  </div>
  <label
    v-if="training.mark?.status === 'in_progress'"
    class="training-field"
  >Progression
    <input
      type="text"
      maxlength="80"
      placeholder="module 4/12"
      :value="training.mark.progress ?? ''"
      data-test="progress"
      @change="emit('mark', 'in_progress', { progress: inputValue($event) })"
    >
  </label>
  <div
    v-if="training.mark?.status === 'done'"
    class="training-field"
  >
    <label>Terminée le
      <input
        type="date"
        :value="training.mark.done_at ?? ''"
        @change="emit('mark', 'done', { done_at: inputValue($event) || null })"
      >
    </label>
    <label class="check">
      <input
        type="checkbox"
        :checked="training.mark.certified ?? false"
        data-test="certified"
        @change="emit('mark', 'done', { certified: !(training.mark.certified ?? false) })"
      > certificat obtenu
    </label>
  </div>
  <div
    v-if="training.mark?.status === 'done'"
    class="training-profile"
    data-test="training-profile"
  >
    <RouterLink
      v-if="training.mark.chunk_id"
      to="/profil?onglet=parcours"
      class="link"
      data-test="in-profile"
    >
      Dans ton profil
    </RouterLink>
    <button
      v-else-if="!drafting"
      type="button"
      class="secondary small"
      data-test="add-to-profile"
      @click="startDraft"
    >
      Ajouter à mon profil
    </button>
    <form
      v-else
      class="training-block-form"
      data-test="block-form"
      @submit.prevent="save"
    >
      <label>Titre du bloc
        <input
          v-model="block.title"
          maxlength="200"
          required
          data-test="block-title"
        >
      </label>
      <label>Texte
        <textarea
          v-model="block.content"
          rows="4"
          maxlength="20000"
          required
          data-test="block-content"
        />
      </label>
      <label>Mots-clés (séparés par des virgules)
        <input
          v-model="block.tags"
          data-test="block-tags"
        >
      </label>
      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
      <div class="training-actions">
        <button
          type="submit"
          class="secondary small"
          :disabled="saving"
          data-test="block-save"
        >
          Enregistrer dans mon profil
        </button>
        <button
          type="button"
          class="link"
          @click="drafting = false"
        >
          Annuler
        </button>
        <HelpTip
          label="Aide : bloc de profil"
          text="Le bloc rejoint Mon parcours et sert aux lettres, aux CV et à la note des offres. Les notes existantes ne sont refaites qu'avec « Renoter » (Réglages › IA)."
        />
      </div>
    </form>
  </div>
</template>
