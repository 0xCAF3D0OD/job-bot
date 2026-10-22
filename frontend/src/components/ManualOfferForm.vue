<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { api } from "../api/client";
import { plural } from "../format";
import { usePlan } from "../composables/usePlan";

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

async function read(): Promise<void> {
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

async function add(): Promise<void> {
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
      error.value = typeof detail === "string" ? detail : "Ajout impossible : vérifie le titre du poste.";
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
    <label v-if="mode === 'link'">Lien de l'annonce
      <input
        v-model="url"
        type="url"
        inputmode="url"
        maxlength="2000"
        required
        :placeholder="linkExample"
        data-test="manual-url"
      >
      <span class="hint">Une offre vue dans Google Jobs : son bouton « Postuler » mène à la page à copier.</span>
    </label>
    <label v-else>Texte de l'annonce
      <textarea
        v-model="text"
        rows="7"
        maxlength="20000"
        required
        :placeholder="textExample"
        data-test="manual-text"
      />
      <span class="hint">{{ plan?.unlimited ? "Lu par l'IA, environ 0,01 $, compté dans ton plafond." : "Lu par l'IA." }} Tes coordonnées ne partent pas.</span>
    </label>
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
      <button
        type="submit"
        class="primary"
        :disabled="reading || full"
        data-test="manual-read"
      >
        {{ reading ? "Lecture…" : "Lire l'annonce" }}
      </button>
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
    <label>Poste
      <input
        v-model="draft.title"
        maxlength="300"
        required
        :placeholder="tradeName || 'Intitulé du poste'"
        type="text"
        data-test="manual-title"
      >
    </label>
    <label>Entreprise
      <input
        v-model="draft.company"
        maxlength="300"
        autocomplete="organization"
        placeholder="Entreprise SA"
        type="text"
        data-test="manual-company"
      >
    </label>
    <label>Lieu et taux
      <input
        v-model="draft.location"
        maxlength="300"
        placeholder="Lausanne 80-100 %"
        type="text"
        data-test="manual-location"
      >
    </label>
    <label>Lien de l'annonce (facultatif)
      <input
        v-model="draft.url"
        type="url"
        inputmode="url"
        maxlength="2000"
        :placeholder="linkExample"
        data-test="manual-draft-url"
      >
    </label>
    <label>Texte de l'annonce
      <textarea
        v-model="draft.description"
        rows="6"
        maxlength="20000"
        data-test="manual-description"
      />
      <span class="hint">Il sert à la note, à la lettre et au CV adapté.</span>
    </label>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="form-actions">
      <button
        type="submit"
        class="primary"
        :disabled="saving"
        data-test="manual-add"
      >
        {{ saving ? "Ajout…" : "Ajouter l'offre" }}
      </button>
      <button
        type="button"
        class="pill"
        data-test="manual-restart"
        @click="restart"
      >
        Recommencer
      </button>
    </div>
  </form>
</template>
