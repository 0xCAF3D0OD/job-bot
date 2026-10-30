<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api } from "../api/client";
import { offerUndo } from "../composables/useUndo";

// « Cette note ne me correspond pas » (docs/114) : deux questions dans la fiche (trop haute
// ou trop basse, pourquoi) ; puis un bloc de profil à relire, ou un critère en un clic. Rien
// n'est appris en cachette : la correction passe par un bloc visible dans Profil, ou par un
// critère. Envoyée au bout de 6 secondes, sauf « Annuler ».
// `startOpen` : les deux questions tout de suite (dans la feuille du bas ouverte par « ⋯ », téléphone).
const props = withDefaults(defineProps<{ offerId: number; startOpen?: boolean }>(), { startOpen: false });
const emit = defineEmits<{ changed: []; cancel: [] }>();

type Direction = "high" | "low";
type Reason =
  | "not_my_trade"
  | "not_my_level"
  | "sector"
  | "place_rate_contract"
  | "my_trade"
  | "have_experience"
  | "sector_ok"
  | "other";
type Block = { kind: "preference" | "redhibitoire"; title: string; content: string; by_ai: boolean };
type Change = { key: string; label: string; changes: Record<string, unknown> };
type Saved = { direction: Direction; reason: Reason; note?: string | null; chunk_id?: number | null; score_before?: number | null; score?: number | null };

const REASONS: Record<Direction, { value: Reason; label: string }[]> = {
  high: [
    { value: "not_my_trade", label: "Ce n'est pas mon métier" },
    { value: "not_my_level", label: "Pas mon niveau" },
    { value: "sector", label: "Le secteur ne m'intéresse pas" },
    { value: "place_rate_contract", label: "Le lieu, le taux ou le contrat" },
    { value: "other", label: "Autre" },
  ],
  low: [
    { value: "my_trade", label: "C'est bien mon métier" },
    { value: "have_experience", label: "J'ai l'expérience demandée" },
    { value: "sector_ok", label: "Le secteur me plaît" },
    { value: "other", label: "Autre" },
  ],
};
const KIND_LABEL = { preference: "Préférence", redhibitoire: "Rédhibitoire" };

const saved = ref<Saved | null>(null);
const open = ref(props.startOpen);
const direction = ref<Direction | null>(null);
const reason = ref<Reason | null>(null);
const note = ref("");
const loading = ref(false);
const block = ref<Block | null>(null);
const changes = ref<Change[] | null>(null);
const error = ref("");

const savedText = computed(() => {
  const s = saved.value;
  if (!s) return "";
  const label = REASONS[s.direction]?.find((r) => r.value === s.reason)?.label.toLowerCase() ?? "";
  return `Tu as corrigé cette note : trop ${s.direction === "high" ? "haute" : "basse"}, ${label}.`;
});

async function load(): Promise<void> {
  const { data } = await api.GET("/api/offers/{offer_id}/score-correction", { params: { path: { offer_id: props.offerId } } });
  saved.value = (data as Saved | null | undefined) ?? null;
}

function reset(): void {
  open.value = false;
  direction.value = null;
  reason.value = null;
  note.value = "";
  block.value = null;
  changes.value = null;
  error.value = "";
}

// « Annuler » : on referme ; la feuille du bas qui l'entoure se ferme aussi.
function cancel(): void {
  reset();
  emit("cancel");
}

watch(() => props.offerId, () => {
  reset();
  void load();
});
onMounted(() => void load());

function choose(value: Direction): void {
  direction.value = value;
  reason.value = null;
  block.value = null;
  changes.value = null;
}

async function propose(value: Reason): Promise<void> {
  reason.value = value;
  if (value === "other" && !note.value.trim()) return;
  if (!direction.value) return;
  loading.value = true;
  error.value = "";
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/score-correction/proposal", {
      params: { path: { offer_id: props.offerId } },
      body: { direction: direction.value, reason: value, note: note.value.trim() || null },
    });
    if (!data) {
      error.value = "La correction n'a pas pu être préparée. Réessaie.";
      return;
    }
    block.value = data.block ? { ...data.block } : null;
    changes.value = data.block ? null : (data.criteria as Change[]);
  } finally {
    loading.value = false;
  }
}

// Envoyée au bout de 6 secondes (docs/108) ; la fiche montre aussitôt la correction.
function send(body: { block?: Omit<Block, "by_ai"> | null; criteria?: Record<string, unknown> | null }, message: string): void {
  if (!direction.value || !reason.value) return;
  const before = saved.value;
  const payload = { direction: direction.value, reason: reason.value, note: note.value.trim() || null, ...body };
  saved.value = { direction: payload.direction, reason: payload.reason };
  reset();
  void offerUndo({
    message,
    commit: async (keepalive) => {
      const { data } = await api.PUT("/api/offers/{offer_id}/score-correction", {
        params: { path: { offer_id: props.offerId } },
        body: payload,
        keepalive,
      });
      if (!data) return false;
      saved.value = data as Saved;
      emit("changed");
      return true;
    },
    restore: () => {
      saved.value = before;
    },
  });
}

function addBlock(): void {
  const b = block.value;
  if (!b || !b.title.trim() || !b.content.trim()) return;
  send({ block: { kind: b.kind, title: b.title.trim(), content: b.content.trim() } }, "Bloc ajouté à ton profil : l'offre va être renotée.");
}

function applyChange(change: Change): void {
  send({ criteria: change.changes }, `${change.label} : critère enregistré.`);
}
</script>

<template>
  <div
    class="score-correction"
    data-test="score-correction"
  >
    <p
      v-if="saved && !open"
      class="hint"
      data-test="score-correction-saved"
    >
      {{ savedText }}
    </p>
    <button
      v-if="!open"
      type="button"
      class="link"
      data-test="score-correction-open"
      @click="open = true"
    >
      {{ saved ? "Corriger à nouveau" : "Cette note ne me correspond pas" }}
    </button>

    <div
      v-else
      class="score-correction-card"
    >
      <p class="score-correction-question">
        <strong>Écart</strong>
      </p>
      <div class="pill-row">
        <button
          v-for="value in (['high', 'low'] as const)"
          :key="value"
          type="button"
          :class="['pill', { selected: direction === value }]"
          :aria-pressed="direction === value"
          :data-test="`score-correction-${value}`"
          @click="choose(value)"
        >
          {{ value === "high" ? "Trop haute" : "Trop basse" }}
        </button>
      </div>

      <template v-if="direction && !block && !changes">
        <p class="score-correction-question">
          <strong>Raison</strong>
        </p>
        <div class="pill-row">
          <button
            v-for="item in REASONS[direction]"
            :key="item.value"
            type="button"
            :class="['pill', { selected: reason === item.value }]"
            :aria-pressed="reason === item.value"
            :disabled="loading"
            :data-test="`score-correction-reason-${item.value}`"
            @click="propose(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
        <label
          v-if="reason === 'other'"
          class="score-correction-note"
        >
          En quelques mots
          <input
            v-model="note"
            type="text"
            maxlength="200"
            data-test="score-correction-note"
            @keydown.enter.prevent="propose('other')"
          >
          <button
            type="button"
            class="pill"
            :disabled="!note.trim() || loading"
            data-test="score-correction-other"
            @click="propose('other')"
          >
            Continuer
          </button>
        </label>
        <p
          v-if="loading"
          class="hint"
          role="status"
        >
          Je prépare la correction…
        </p>
      </template>

      <!-- Un bloc de profil à relire avant de l'ajouter. -->
      <div
        v-if="block"
        class="score-correction-block"
        data-test="score-correction-block"
      >
        <p class="setting-desc">
          Ce bloc rejoindra ton profil et comptera dès la prochaine note.
        </p>
        <span class="badge">{{ KIND_LABEL[block.kind] }}</span>
        <label>Titre
          <input
            v-model="block.title"
            type="text"
            maxlength="200"
            data-test="score-correction-title"
          >
        </label>
        <label>Ce que l'IA lira
          <textarea
            v-model="block.content"
            rows="3"
            maxlength="2000"
            data-test="score-correction-content"
          />
        </label>
        <div class="pill-row">
          <button
            type="button"
            class="primary"
            :disabled="!block.title.trim() || !block.content.trim()"
            data-test="score-correction-add"
            @click="addBlock"
          >
            Ajouter à mon profil
          </button>
          <button
            type="button"
            class="pill"
            data-test="score-correction-cancel"
            @click="cancel"
          >
            Annuler
          </button>
        </div>
      </div>

      <!-- Lieu, taux, contrat : un critère, en un clic. -->
      <div
        v-if="changes"
        class="score-correction-block"
        data-test="score-correction-criteria"
      >
        <p class="setting-desc">
          Ce n'est pas l'affaire de l'IA : un critère écarte ces offres, sans note.
        </p>
        <div class="pill-row">
          <button
            v-for="change in changes"
            :key="change.key"
            type="button"
            class="pill"
            :data-test="`score-correction-change-${change.key}`"
            @click="applyChange(change)"
          >
            {{ change.label }}
          </button>
          <RouterLink
            to="/profil"
            class="pill"
            data-test="score-correction-criteria-link"
          >
            Régler mes critères
          </RouterLink>
        </div>
        <button
          type="button"
          class="link"
          @click="cancel"
        >
          Annuler
        </button>
      </div>

      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
      <button
        v-if="!block && !changes"
        type="button"
        class="link"
        data-test="score-correction-close"
        @click="cancel"
      >
        Annuler
      </button>
    </div>
  </div>
</template>
