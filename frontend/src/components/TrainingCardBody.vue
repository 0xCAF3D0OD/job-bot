<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import { api, type Training } from "../api/client";
import { onDay } from "../format";
import { highlight, languageLabel } from "../newsLabels";
import { FORMATS, KINDS, LEVELS, PRICES, SHORT_FORMATS, STATUSES } from "../trainingLabels";
import AppIcon from "./AppIcon.vue";
import CopyLabel from "./CopyLabel.vue";
import IconButton from "./IconButton.vue";
import StatusPill from "./StatusPill.vue";

// Contenu d'une formation (docs/16 §5). Deux présentations (docs/44) : la carte du catalogue,
// calme (description sur 3 lignes, une ligne en bas : « Suivre », ou l'état et « Gérer ») ;
// le panneau latéral, avec tout le suivi en trois sections (Suivi, Financement ORP,
// Profil).
export type TrainingStatus = "interested" | "in_progress" | "done";
export type MarkExtra = { progress?: string | null; done_at?: string | null; certified?: boolean | null };
type Status = TrainingStatus;

const props = withDefaults(defineProps<{ training: Training; variant?: "card" | "panel" }>(), { variant: "card" });
const emit = defineEmits<{
  // Carte : « Suivre » ou « Gérer » ouvre le panneau latéral.
  manage: [];
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

// Demande de financement à l'ORP (docs/37 §2) : un texte sans IA, avec l'argument tiré de
// tes offres, à copier ; puis le suivi (demandée, acceptée, refusée).
type Funding = NonNullable<NonNullable<Training["mark"]>["funding_status"]>;
// En pastille (§4) : acceptée en vert ; demandée ou refusée en neutre (un refus n'est pas une erreur).
const FUNDING_TONES: Record<Funding, "neutral" | "ok"> = { requested: "neutral", accepted: "ok", refused: "neutral" };
const FUNDING_LABELS: Record<Funding, string> = {
  requested: "Financement demandé",
  accepted: "Financement accepté",
  refused: "Financement refusé",
};
const letter = ref("");
const preparing = ref(false);
const copied = ref(false);
const fundingError = ref("");

function argumentText(offers: number, matched: string[], examples: { title: string; company: string | null }[]): string {
  if (!offers) return "";
  const asked = matched.length ? matched.join(" ou ") : "ce que la formation apporte";
  const samples = examples.map((e) => `« ${e.title} »${e.company ? ` chez ${e.company}` : ""}`);
  const sample = samples.length ? `, par exemple ${samples.join(" et ")}` : "";
  return `Elle répond à ce que demandent les offres de mon domaine : sur les 90 derniers jours, ${offers === 1 ? "1 offre que j'ai reçue demandait" : `${offers} offres que j'ai reçues demandaient`} ${asked}${sample}.`;
}

async function prepareRequest(): Promise<void> {
  preparing.value = true;
  fundingError.value = "";
  try {
    const { data } = await api.GET("/api/trainings/{training_id}/funding-request", {
      params: { path: { training_id: props.training.id } },
    });
    if (!data) {
      fundingError.value = "Préparation impossible pour l'instant.";
      return;
    }
    const t = props.training;
    const facts = [FORMATS[t.format] ?? t.format, `en ${languageLabel(t.language)}`].join(", ");
    letter.value = [
      "Bonjour [nom du conseiller],",
      `Je souhaite suivre la formation « ${t.title} » (${t.provider}, ${facts}) : ${t.url}`,
      argumentText(data.offers, data.matched, data.examples),
      `Coût : [montant]. Durée : ${t.duration ?? "[durée]"}.`,
      "Pourriez-vous me dire si elle peut être prise en charge au titre des mesures relatives au marché du travail ?",
      data.sender ?? "[ton prénom et nom]",
    ]
      .filter(Boolean)
      .join("\n\n");
  } finally {
    preparing.value = false;
  }
}

async function copyLetter(): Promise<void> {
  try {
    await navigator.clipboard.writeText(letter.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    copied.value = false;
  }
}

async function setFunding(status: Funding | null): Promise<void> {
  fundingError.value = "";
  const { data } = await api.PUT("/api/trainings/{training_id}/funding", {
    params: { path: { training_id: props.training.id } },
    body: { status },
  });
  if (!data) {
    fundingError.value = "Enregistrement impossible.";
    return;
  }
  if (status === "requested") letter.value = "";
  emit("linked", data);
}

function day(value: string): string {
  return onDay(`${value}T12:00:00`);
}

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

// La pastille d'état de la carte : « En cours · module 6/12 », « Terminée · certificat ».
const stateText = computed(() => {
  const mark = props.training.mark;
  if (!mark) return "";
  const detail =
    mark.status === "in_progress" ? mark.progress : mark.status === "done" && mark.certified ? "certificat" : null;
  return detail ? `${STATUSES[mark.status]} · ${detail}` : (STATUSES[mark.status] ?? "");
});
</script>

<template>
  <div class="training-head">
    <span class="news-meta meta-line">
      <span>{{ KINDS[training.kind] }}</span>
      <span><AppIcon name="building" /><span class="visually-hidden">Organisme : </span>{{ training.provider }}</span>
    </span>
    <StatusPill
      v-if="training.mark?.funding_status"
      :tone="FUNDING_TONES[training.mark.funding_status]"
      data-test="funding-badge"
    >
      {{ FUNDING_LABELS[training.mark.funding_status] }}
    </StatusPill>
    <StatusPill
      v-if="!training.verified"
      tone="todo"
      data-test="unverified"
    >
      À vérifier
    </StatusPill>
  </div>
  <!-- Panneau : le titre est déjà en tête ; ici, le lien vers la page officielle. -->
  <a
    v-if="variant === 'panel'"
    class="link"
    :href="training.url"
    target="_blank"
    rel="noopener noreferrer"
    data-test="official-page"
  ><span class="with-icon"><AppIcon name="external" />Page officielle<span class="visually-hidden"> (nouvel onglet)</span></span></a>
  <a
    v-else
    class="training-title"
    :href="training.url"
    target="_blank"
    rel="noopener noreferrer"
  ><template
    v-for="(part, index) in highlight(training.title, training.matched)"
    :key="index"
  ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></a>
  <!-- Les faits avec les icônes de la carte (docs/101) : le mot reste pour un lecteur d'écran. -->
  <p
    class="training-facts meta-line"
    data-test="training-facts"
  >
    <span><AppIcon name="globe" /><span class="visually-hidden">Format et langue : </span><span :title="FORMATS[training.format]">{{ SHORT_FORMATS[training.format] ?? FORMATS[training.format] }}</span>, {{ languageLabel(training.language) }}</span>
    <span><AppIcon name="tag" /><span class="visually-hidden">Prix : </span>{{ PRICES[training.price] }}</span>
    <span v-if="training.level"><AppIcon name="stats" /><span class="visually-hidden">Niveau : </span>{{ LEVELS[training.level] }}</span>
    <span v-if="training.duration"><AppIcon name="clock" /><span class="visually-hidden">Durée : </span>{{ training.duration }}</span>
  </p>
  <p
    v-if="training.description"
    :class="['training-text', { clamped: variant === 'card' }]"
  >
    {{ training.description }}
  </p>
  <p
    v-if="training.prep && variant === 'panel'"
    class="training-text"
  >
    <strong>Préparation conseillée :</strong> {{ training.prep }}
  </p>
  <div
    v-if="!training.verified"
    class="training-actions"
  >
    <IconButton
      icon="bookmark"
      label="Garder"
      data-test="keep"
      @click="emit('review', true)"
    />
    <IconButton
      icon="trash"
      label="Écarter"
      danger
      data-test="dismiss"
      @click="emit('review', false)"
    />
  </div>
  <div
    v-if="variant === 'card'"
    class="training-foot"
    data-test="training-foot"
  >
    <IconButton
      v-if="!training.mark"
      icon="bookmark"
      label="Suivre"
      data-test="follow"
      @click="emit('manage')"
    />
    <template v-else>
      <span
        class="training-state"
        data-test="training-state"
      >{{ stateText }}</span>
      <button
        type="button"
        class="link"
        data-test="manage"
        @click="emit('manage')"
      >
        Gérer
      </button>
    </template>
  </div>
  <template v-else>
    <section
      class="panel-section"
      data-test="section-follow"
    >
      <h3>Suivi</h3>
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
    </section>
    <section
      v-if="training.price === 'paid' && training.mark"
      class="panel-section"
      data-test="section-funding"
    >
      <h3>Financement ORP</h3>
      <div
        class="training-funding"
        data-test="training-funding"
      >
        <template v-if="!training.mark.funding_status">
          <button
            v-if="!letter"
            type="button"
            class="secondary small"
            :disabled="preparing"
            data-test="prepare-funding"
            @click="prepareRequest"
          >
            <span class="with-icon"><AppIcon name="file" />{{ preparing ? "Préparation…" : "Préparer la demande à l'ORP" }}</span>
          </button>
          <template v-else>
            <textarea
              v-model="letter"
              rows="10"
              aria-label="Demande de financement à ton conseiller ORP"
              data-test="funding-letter"
            />
            <div class="training-actions">
              <button
                type="button"
                class="link"
                data-test="funding-copy"
                @click="copyLetter"
              >
                <CopyLabel :done="copied" />
              </button>
              <button
                type="button"
                class="secondary small"
                data-test="funding-requested"
                @click="setFunding('requested')"
              >
                Marquer comme demandée
              </button>
            </div>
          </template>
        </template>
        <div
          v-else
          class="training-actions"
        >
          <span
            v-if="training.mark.funding_status === 'requested' && training.mark.funding_requested_at"
            class="muted"
          >Demandée {{ day(training.mark.funding_requested_at) }}</span>
          <template v-if="training.mark.funding_status === 'requested'">
            <button
              type="button"
              class="secondary small"
              data-test="funding-accepted"
              @click="setFunding('accepted')"
            >
              Acceptée
            </button>
            <button
              type="button"
              class="secondary small"
              data-test="funding-refused"
              @click="setFunding('refused')"
            >
              Refusée
            </button>
          </template>
          <button
            type="button"
            class="link"
            data-test="funding-reset"
            @click="setFunding(null)"
          >
            {{ training.mark.funding_status === "requested" ? "Retirer la demande" : "Modifier" }}
          </button>
        </div>
        <p
          v-if="fundingError"
          class="notice error"
          role="alert"
        >
          {{ fundingError }}
        </p>
      </div>
    </section>
    <section
      v-if="training.mark?.status === 'done'"
      class="panel-section"
      data-test="section-profile"
    >
      <h3>Profil</h3>
      <div
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
          </div>
        </form>
      </div>
    </section>
  </template>
</template>
