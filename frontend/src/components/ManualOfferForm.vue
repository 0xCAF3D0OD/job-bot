<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from "vue";

import { api } from "../api/client";
import { plural } from "../format";
import { usePlan } from "../composables/usePlan";
import BusyButton from "./BusyButton.vue";
import FormField from "./FormField.vue";

const { plan } = usePlan();

// Ajouter une offre trouvée ailleurs (docs/111) : un lien ou un texte, lu par la page
// (balisage JobPosting) ou par l'IA ; une fiche à relire ; puis l'offre, filtrée et notée
// comme les autres. Les exemples suivent le métier de la personne, pas un métier inventé.
const props = defineProps<{ initialUrl?: string | null; initialText?: string | null }>();
const emit = defineEmits<{ added: [result: { id: number; existing: boolean; status: string; reasons: string[] }] }>();

type Mode = "link" | "text";
type ReadBy = "page" | "ia" | "main";
const mode = ref<Mode>(props.initialText && !props.initialUrl ? "text" : "link");
const url = ref(props.initialUrl ?? "");
const text = ref(props.initialText ?? "");
const reading = ref(false);
const saving = ref(false);
const problem = ref("");
const error = ref("");

const trade = ref<string | null>(null);
const addedToday = ref(0);
const limit = ref(20);

const draft = reactive({ title: "", company: "", location: "", description: "", url: "" });
const shown = ref(false);
const readBy = ref<ReadBy>("main");
const matchesTrade = ref(true);
const existingId = ref<number | null>(null);

onMounted(async () => {
  const { data } = await api.GET("/api/offers/manual");
  if (!data) return;
  trade.value = data.trade ?? null;
  addedToday.value = data.added_today;
  limit.value = data.daily_limit;
});

// Exemples tirés du métier : « Menuisier » donne « https://entreprise.ch/emplois/menuisier ».
const tradeName = computed(() => trade.value?.trim() || "");
const slug = computed(() =>
  (tradeName.value || "poste")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, ""),
);
const linkExample = computed(() => `https://entreprise.ch/emplois/${slug.value}`);
const textExample = computed(() =>
  tradeName.value
    ? `Colle ici le texte de l'annonce, par exemple : « ${tradeName.value} (80-100 %), Entreprise SA, Lausanne. Tes missions… »`
    : "Colle ici le texte de l'annonce : poste, entreprise, lieu, missions…",
);
const full = computed(() => addedToday.value >= limit.value);
const textHint = computed(
  () => `${plan.value?.unlimited ? "Lu par l'IA, environ 0,01 $, compté dans ton plafond." : "Lu par l'IA."} Tes coordonnées ne partent pas.`,
);

// Règles §4 (Champ de formulaire, Formulaire) : l'erreur sous le champ, en le quittant puis à
// l'envoi, et dit quoi faire ; à l'envoi, le curseur va au premier champ en erreur.
type Field = "url" | "text" | "title";
const MISSING: Record<Field, string> = {
  url: "Colle le lien de l'annonce.",
  text: "Colle le texte de l'annonce.",
  title: "Indique le poste.",
};
const errors = ref<Partial<Record<Field, string>>>({});
function valueOf(field: Field): string {
  return field === "url" ? url.value : field === "text" ? text.value : draft.title;
}
function check(field: Field): void {
  const next = { ...errors.value };
  if (valueOf(field).trim()) delete next[field];
  else next[field] = MISSING[field];
  errors.value = next;
}
function clearIfFixed(field: Field): void {
  if (errors.value[field]) check(field);
}
async function valid(form: EventTarget | null, field: Field): Promise<boolean> {
  check(field);
  if (!errors.value[field]) return true;
  await nextTick();
  (form as HTMLElement | null)?.querySelector<HTMLElement>("[aria-invalid='true']")?.focus();
  return false;
}

async function read(event: Event): Promise<void> {
  if (!(await valid(event.currentTarget, mode.value === "link" ? "url" : "text"))) return;
  problem.value = "";
  error.value = "";
  reading.value = true;
  try {
    const body = mode.value === "link" ? { url: url.value.trim() } : { text: text.value };
    const { data } = await api.POST("/api/offers/manual/read", { body });
    if (!data) {
      problem.value = "Lecture impossible pour l'instant : réessaie, ou remplis la fiche à la main.";
      return;
    }
    if (!data.draft) {
      problem.value = data.problem ?? "Lecture impossible.";
      // Page protégée ou illisible : on passe au texte, le lien gardé pour la fiche.
      if (data.paste) mode.value = "text";
      return;
    }
    const d = data.draft;
    Object.assign(draft, {
      title: d.title,
      company: d.company ?? "",
      location: d.location ?? "",
      description: d.description ?? "",
      url: d.url ?? (url.value.trim() || ""),
    });
    readBy.value = d.read_by;
    matchesTrade.value = d.matches_trade;
    existingId.value = d.existing_offer_id ?? null;
    shown.value = true;
  } finally {
    reading.value = false;
  }
}

// Sans IA ou sans annonce lisible : la fiche vide, à remplir soi-même.
function byHand(): void {
  Object.assign(draft, {
    title: "",
    company: "",
    location: "",
    description: mode.value === "text" ? text.value.trim() : "",
    url: url.value.trim(),
  });
  readBy.value = "main";
  matchesTrade.value = true;
  existingId.value = null;
  problem.value = "";
  shown.value = true;
}

function restart(): void {
  shown.value = false;
  error.value = "";
}

async function add(event: Event): Promise<void> {
  if (!(await valid(event.currentTarget, "title"))) return;
  error.value = "";
  saving.value = true;
  try {
    const { data, error: refused } = await api.POST("/api/offers/manual", {
      body: {
        title: draft.title,
        company: draft.company.trim() || null,
        location: draft.location.trim() || null,
        description: draft.description.trim() || null,
        url: draft.url.trim() || null,
        read_by: readBy.value,
      },
    });
    if (!data) {
      const detail = (refused as { detail?: unknown } | undefined)?.detail;
      error.value = typeof detail === "string" ? detail : "Ajout impossible pour l'instant : réessaie.";
      return;
    }
    emit("added", data);
  } finally {
    saving.value = false;
  }
}

function openExisting(): void {
  if (existingId.value !== null) emit("added", { id: existingId.value, existing: true, status: "", reasons: [] });
}
</script>

<template>
  <form
    v-if="!shown"
    class="manual-form"
    data-test="manual-form"
    novalidate
    @submit.prevent="read"
  >
    <p class="setting-desc">
      Une annonce vue ailleurs : jobA1 la lit, tu la relis, elle rejoint tes offres.
    </p>
    <div
      class="segmented"
      role="radiogroup"
      aria-label="Ce que tu ajoutes"
    >
      <button
        type="button"
        role="radio"
        :aria-checked="mode === 'link'"
        data-test="manual-mode-link"
        @click="mode = 'link'"
      >
        Un lien
      </button>
      <button
        type="button"
        role="radio"
        :aria-checked="mode === 'text'"
        data-test="manual-mode-text"
        @click="mode = 'text'"
      >
        Un texte
      </button>
    </div>
    <FormField
      v-if="mode === 'link'"
      v-slot="{ id, describedby, invalid }"
      label="Lien de l'annonce"
      hint="Une offre vue dans Google Jobs : son bouton « Postuler » mène à la page à copier."
      :error="errors.url"
    >
      <input
        :id="id"
        v-model="url"
        type="url"
        inputmode="url"
        maxlength="2000"
        required
        :placeholder="linkExample"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-url"
        @blur="check('url')"
        @input="clearIfFixed('url')"
      >
    </FormField>
    <FormField
      v-else
      v-slot="{ id, describedby, invalid }"
      label="Texte de l'annonce"
      :hint="textHint"
      :error="errors.text"
    >
      <textarea
        :id="id"
        v-model="text"
        rows="7"
        maxlength="20000"
        required
        :placeholder="textExample"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-text"
        @blur="check('text')"
        @input="clearIfFixed('text')"
      />
    </FormField>
    <p
      v-if="problem"
      class="notice"
      role="alert"
      data-test="manual-problem"
    >
      {{ problem }}
      <button
        type="button"
        class="link"
        data-test="manual-by-hand"
        @click="byHand"
      >
        Remplir la fiche à la main
      </button>
    </p>
    <div class="form-actions">
      <BusyButton
        type="submit"
        class="primary"
        :busy="reading"
        busy-label="Lecture…"
        :disabled="full"
        data-test="manual-read"
      >
        Lire l'annonce
      </BusyButton>
    </div>
    <p
      class="hint"
      data-test="manual-count"
    >
      {{ full ? `${limit} offres ajoutées en 24 heures : c'est le maximum, reviens demain.` : `${plural(addedToday, "offre ajoutée", "offres ajoutées")} sur ${limit} ces 24 heures.` }}
    </p>
  </form>

  <form
    v-else
    class="manual-form"
    data-test="manual-draft"
    novalidate
    @submit.prevent="add"
  >
    <p class="setting-desc">
      {{ readBy === "page" ? "Lue sur la page de l'annonce." : readBy === "ia" ? "Lue par l'IA." : "À remplir toi-même." }}
      Corrige au besoin, puis ajoute-la.
    </p>
    <p
      v-if="existingId !== null"
      class="notice"
      data-test="manual-existing"
    >
      Cette offre est déjà dans tes offres.
      <button
        type="button"
        class="link"
        @click="openExisting"
      >
        L'ouvrir
      </button>
    </p>
    <p
      v-else-if="!matchesTrade && tradeName"
      class="notice"
      data-test="manual-off-trade"
    >
      Cette annonce ne parle pas de « {{ tradeName }} » : la note dira si elle te correspond.
    </p>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Poste"
      :error="errors.title"
    >
      <input
        :id="id"
        v-model="draft.title"
        maxlength="300"
        required
        :placeholder="tradeName || undefined"
        type="text"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-title"
        @blur="check('title')"
        @input="clearIfFixed('title')"
      >
    </FormField>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Entreprise"
      optional
      :width="20"
    >
      <input
        :id="id"
        v-model="draft.company"
        maxlength="300"
        autocomplete="organization"
        placeholder="Entreprise SA"
        type="text"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-company"
      >
    </FormField>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Lieu et taux"
      optional
      :width="30"
    >
      <input
        :id="id"
        v-model="draft.location"
        maxlength="300"
        placeholder="Lausanne 80-100 %"
        type="text"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-location"
      >
    </FormField>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Lien de l'annonce"
      optional
    >
      <input
        :id="id"
        v-model="draft.url"
        type="url"
        inputmode="url"
        maxlength="2000"
        :placeholder="linkExample"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-draft-url"
      >
    </FormField>
    <FormField
      v-slot="{ id, describedby, invalid }"
      label="Texte de l'annonce"
      optional
      hint="Il sert à la note, à la lettre et au CV adapté."
    >
      <textarea
        :id="id"
        v-model="draft.description"
        rows="6"
        maxlength="20000"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-description"
      />
    </FormField>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="form-actions">
      <BusyButton
        type="submit"
        class="primary"
        :busy="saving"
        busy-label="Ajout…"
        data-test="manual-add"
      >
        Ajouter l'offre
      </BusyButton>
      <button
        type="button"
        class="secondary"
        data-test="manual-restart"
        @click="restart"
      >
        Recommencer
      </button>
    </div>
  </form>
</template>
