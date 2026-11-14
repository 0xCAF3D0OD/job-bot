<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from "vue";

import { api } from "../api/client";
import type { ComposerItem } from "../composer";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import AppIcon from "./AppIcon.vue";
import Composer from "./Composer.vue";
import FormField from "./FormField.vue";

const { plan } = usePlan();

// Ajouter une offre trouvée ailleurs (docs/111) : un lien ou un texte, lu par la page
// (balisage JobPosting) ou par l'IA ; une fiche à relire ; puis l'offre, filtrée et notée
// comme les autres. Maquette du 8 novembre
// (docs/143, D25) : la zone de saisie commune de 3 lignes, « Lien ou texte de l'annonce » ; un lien seul est lu comme
// un lien, tout le reste comme un texte.
// Paquet du 11 novembre, PR 38 (maquette CandidaturesOrdinateurAjouter) : sur ordinateur, un champ à libellé flottant
// sans flèche d'envoi ; le seul bouton est « Ajouter l'offre », dans le pied du panneau (il envoie ce formulaire par
// son `formId`). Une fois l'annonce lue, le champ reste, et « Ce que jobA1 a lu » vient dessous : Poste, Entreprise,
// Lieu, Contrat, puis la ligne repliable « Texte lu ». Changer le champ fait relire : plus de « Recommencer ».
// « Importer le PDF de l'annonce » (décision de Kevin du 11 novembre) : le serveur en tire le texte, sans IA, et ne
// garde pas le fichier (E-5, J-1) ; le texte arrive dans le champ, comme un texte collé. Pas de capture d'écran.
const props = withDefaults(defineProps<{ initialUrl?: string | null; initialText?: string | null; formId?: string }>(), {
  initialUrl: null,
  initialText: null,
  formId: undefined,
});
const emit = defineEmits<{
  added: [result: { id: number; existing: boolean; status: string; reasons: string[]; filled?: string[] }];
}>();

type Mode = "link" | "text";
type ReadBy = "page" | "ia" | "main";
const mode = ref<Mode>(props.initialText && !props.initialUrl ? "text" : "link");
const url = ref(props.initialUrl ?? "");
const text = ref(props.initialText ?? "");
// Ce que la personne colle : un lien ou le texte de l'annonce.
const entry = ref(props.initialUrl || props.initialText || "");
const entryError = ref("");
const LINK = /^https?:\/\/\S+$/i;
const reading = ref(false);
const saving = ref(false);
const problem = ref("");
const error = ref("");

const trade = ref<string | null>(null);
const addedToday = ref(0);
const limit = ref(20);

const UNKNOWN_CONTRACT = "Non précisé";
const draft = reactive({ title: "", company: "", location: "", contract: UNKNOWN_CONTRACT, description: "", url: "" });
// Ce qui a été lu : tant que le champ ne change pas, « Ajouter l'offre » ajoute ; sinon il relit.
const readEntry = ref("");
const textOpen = ref(false);
const shown = ref(false);
const readBy = ref<ReadBy>("main");
const matchesTrade = ref(true);
const existingId = ref<number | null>(null);
// Déjà là, avec des champs vides que cette annonce remplit (son texte, son lien…) : « Compléter
// l'offre » les ajoute, sans rien remplacer (demande de Kevin, 2026-11-05).
type Fillable = "company" | "location" | "description" | "url";
const fillable = ref<Fillable[]>([]);
const FILLABLE_WORDS: Record<Fillable, string> = {
  company: "l’entreprise",
  location: "le lieu",
  description: "le texte de l’annonce",
  url: "le lien",
};
const completing = computed(() => existingId.value !== null && fillable.value.length > 0);
const missingWords = computed(() => {
  const words = fillable.value.map((f) => FILLABLE_WORDS[f]);
  return words.length > 1 ? `${words.slice(0, -1).join(", ")} et ${words.at(-1)}` : (words[0] ?? "");
});

onMounted(async () => {
  const { data } = await api.GET("/api/offers/manual");
  if (!data) return;
  trade.value = data.trade ?? null;
  addedToday.value = data.added_today;
  limit.value = data.daily_limit;
});

const tradeName = computed(() => trade.value?.trim() || "");
const full = computed(() => addedToday.value >= limit.value);
const left = computed(() => Math.max(0, limit.value - addedToday.value));
const countLine = computed(() =>
  full.value
    ? `${limit.value} offres ajoutées en 24 heures : c’est le maximum, reviens demain.`
    : `Tu peux encore en ajouter ${left.value === 1 ? "une" : left.value} aujourd’hui.`,
);
const textHint = computed(
  () => `${plan.value?.unlimited ? "Lu par l’IA, environ 0,01 $, compté dans ton plafond." : "Lu par l’IA."} Tes coordonnées ne partent pas.`,
);

// Règles §4 (Champ de formulaire, Formulaire) : l'erreur sous le champ, en le quittant puis à
// l'envoi, et dit quoi faire ; à l'envoi, le curseur va au premier champ en erreur.
type Field = "url" | "text" | "title";
const MISSING: Record<Field, string> = {
  url: "Colle le lien de l’annonce.",
  text: "Colle le texte de l’annonce.",
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

async function read(value: string = entry.value): Promise<void> {
  const typed = value.trim();
  if (!typed) {
    entryError.value = "Colle le lien ou le texte de l’annonce.";
    return;
  }
  entryError.value = "";
  // Après une page illisible, le texte collé s'ajoute au lien gardé.
  if (LINK.test(typed)) {
    mode.value = "link";
    url.value = typed;
  } else {
    mode.value = "text";
    text.value = typed;
  }
  problem.value = "";
  error.value = "";
  reading.value = true;
  try {
    const body = mode.value === "link" ? { url: url.value.trim() } : { text: text.value };
    const { data } = await api.POST("/api/offers/manual/read", { body });
    if (!data) {
      problem.value = "Lecture impossible pour l’instant : réessaie, ou remplis la fiche à la main.";
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
      contract: d.contract || UNKNOWN_CONTRACT,
      description: d.description ?? "",
      url: d.url ?? (url.value.trim() || ""),
    });
    readBy.value = d.read_by;
    matchesTrade.value = d.matches_trade;
    existingId.value = d.existing_offer_id ?? null;
    fillable.value = d.fillable ?? [];
    // Déjà dans la liste, et rien à lui ajouter : on l'ouvre tout de suite (PR 38), sans fiche à relire.
    if (existingId.value !== null && !fillable.value.length) {
      openExisting();
      return;
    }
    readEntry.value = typed;
    textOpen.value = false;
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
    contract: UNKNOWN_CONTRACT,
    description: mode.value === "text" ? text.value.trim() : "",
    url: url.value.trim(),
  });
  readBy.value = "main";
  matchesTrade.value = true;
  existingId.value = null;
  fillable.value = [];
  problem.value = "";
  readEntry.value = entry.value.trim();
  textOpen.value = true;
  shown.value = true;
}

// Le champ a changé après la lecture : la fiche lue ne vaut plus, « Ajouter l'offre » relira.
function entryChanged(): void {
  if (entryError.value && entry.value.trim()) entryError.value = "";
  pdfProblem.value = "";
  if (shown.value && entry.value.trim() !== readEntry.value) {
    shown.value = false;
    error.value = "";
  }
}

// Le PDF de l'annonce : son texte, lu par le serveur, arrive dans le champ ; la personne le relit, puis ajoute.
const PDF_PROBLEMS: Record<string, string> = {
  "no-text": "Ce PDF ne contient pas de texte. Colle le texte de l’annonce.",
  "too-big": "Ce PDF est trop lourd (5 Mo au plus). Colle le texte de l’annonce.",
  "not-pdf": "Ce fichier n’est pas un PDF. Colle le texte de l’annonce.",
  unreadable: "Ce PDF ne peut pas être lu. Colle le texte de l’annonce.",
};
const PDF_ITEMS: ComposerItem[] = [{ id: "pdf", label: "Importer le PDF de l’annonce", icon: "upload" }];
const MAX_PDF = 5 * 1024 * 1024;
const picker = ref<HTMLInputElement | null>(null);
const importing = ref(false);
const pdfProblem = ref("");
const pdfDone = ref(false);
function pickPdf(): void {
  picker.value?.click();
}
async function importPdf(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || importing.value) return;
  pdfProblem.value = "";
  pdfDone.value = false;
  if (file.size > MAX_PDF) {
    pdfProblem.value = PDF_PROBLEMS["too-big"]!;
    return;
  }
  importing.value = true;
  try {
    const { data, error: refused } = await api.POST("/api/offers/manual/pdf", {
      body: { file: "" },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    if (!data) {
      const detail = (refused as { detail?: unknown } | undefined)?.detail;
      pdfProblem.value = typeof detail === "string" ? detail : "Import impossible pour l’instant : réessaie.";
    } else if (!data.text) {
      pdfProblem.value = PDF_PROBLEMS[data.problem ?? "unreadable"] ?? PDF_PROBLEMS.unreadable!;
    } else {
      entry.value = data.text;
      mode.value = "text";
      entryChanged();
      problem.value = "";
      pdfDone.value = true;
    }
  } finally {
    importing.value = false;
  }
}

async function submit(event: Event): Promise<void> {
  if (reading.value || saving.value || importing.value) return;
  if (shown.value) await add(event);
  else if (!full.value) await read();
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
        contract: contractValue(),
        description: draft.description.trim() || null,
        url: draft.url.trim() || null,
        read_by: readBy.value,
        fill: completing.value,
      },
    });
    if (!data) {
      const detail = (refused as { detail?: unknown } | undefined)?.detail;
      error.value = typeof detail === "string" ? detail : "Ajout impossible pour l’instant : réessaie.";
      return;
    }
    emit("added", data);
  } finally {
    saving.value = false;
  }
}

// « Non précisé » est ce que l'écran montre pour un contrat inconnu : il n'est pas enregistré.
function contractValue(): string | null {
  const value = draft.contract.trim();
  return !value || value.toLowerCase() === UNKNOWN_CONTRACT.toLowerCase() ? null : value;
}
const chars = computed(() => new Intl.NumberFormat("fr-CH").format(draft.description.trim().length).replace(/[’']/g, "\u202f"));
const textLine = computed(
  () => `${chars.value} ${draft.description.trim().length > 1 ? "caractères" : "caractère"}${readBy.value === "page" || (readBy.value === "ia" && mode.value === "link") ? " · cookies et formulaire retirés" : ""}`,
);

function openExisting(): void {
  if (existingId.value !== null) emit("added", { id: existingId.value, existing: true, status: "", reasons: [] });
}
// Maquette du 8 novembre (LISEZMOI, Composer) : 3 lignes sur ordinateur, 4 sur téléphone (AjouterOffreTel).
const { phone } = usePhone();

// Le bouton du pied du panneau (OffersView) : son libellé et son attente.
defineExpose({
  shown,
  full,
  busy: computed(() => reading.value || saving.value),
  label: computed(() => (completing.value && shown.value ? "Compléter l’offre" : "Ajouter l’offre")),
  busyLabel: computed(() => (reading.value ? "Lecture de l’annonce…" : completing.value ? "Ajout des champs…" : "Ajout…")),
});
</script>

<template>
  <form
    :id="formId"
    class="manual-form"
    data-test="manual-form"
    novalidate
    @submit.prevent="submit"
  >
    <Composer
      v-if="phone"
      v-model="entry"
      :rows="4"
      placeholder="Lien ou texte de l’annonce"
      send-label="Ajouter l’offre"
      :busy="reading || full"
      :plus-items="PDF_ITEMS"
      data-test="manual-entry"
      @update:model-value="entryChanged"
      @attach="pickPdf"
      @send="read"
    />
    <FormField
      v-else
      v-slot="{ id, describedby, invalid }"
      label="Lien ou texte de l’annonce"
      :error="entryError"
    >
      <textarea
        :id="id"
        v-model="entry"
        rows="3"
        maxlength="20000"
        class="manual-entry"
        :aria-describedby="describedby"
        :aria-invalid="invalid"
        data-test="manual-entry"
        @input="entryChanged"
      />
    </FormField>
    <p
      v-if="phone && entryError"
      class="field-error"
      role="alert"
      data-test="manual-entry-error"
    >
      {{ entryError }}
    </p>
    <p
      class="hint"
      data-test="manual-count"
    >
      {{ countLine }}
    </p>
    <p
      v-if="reading || importing"
      class="hint"
      role="status"
    >
      {{ importing ? "Lecture du PDF…" : "Lecture de l’annonce…" }}
    </p>
    <p
      v-else-if="pdfDone && !shown"
      class="hint"
      role="status"
      data-test="manual-pdf-done"
    >
      Texte du PDF repris. Relis-le, puis ajoute l’offre.
    </p>
    <p
      v-if="mode === 'text' && !shown && !reading"
      class="hint"
      data-test="manual-text-hint"
    >
      {{ textHint }}
    </p>
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
    <input
      ref="picker"
      type="file"
      accept="application/pdf,.pdf"
      class="visually-hidden"
      tabindex="-1"
      aria-hidden="true"
      data-test="manual-pdf-file"
      @change="importPdf"
    >
    <button
      v-if="!shown && !phone"
      type="button"
      class="secondary manual-pdf"
      :disabled="importing || full"
      data-test="manual-pdf"
      @click="pickPdf"
    >
      <AppIcon name="upload" />Importer le PDF de l’annonce
    </button>
    <p
      v-if="pdfProblem"
      class="notice"
      role="alert"
      data-test="manual-pdf-problem"
    >
      {{ pdfProblem }}
    </p>
    <section
      v-if="shown"
      class="manual-read"
      data-test="manual-draft"
    >
      <h3 class="manual-read-cap">
        {{ readBy === "main" ? "À remplir toi-même" : "Ce que jobA1 a lu" }}
      </h3>
      <p
        v-if="completing"
        class="notice"
        data-test="manual-existing"
      >
        Cette offre est déjà dans tes offres, sans {{ missingWords }} : « Compléter l’offre » les ajoute,
        sans rien remplacer.
        <button
          type="button"
          class="link"
          @click="openExisting"
        >
          L’ouvrir
        </button>
      </p>
      <p
        v-else-if="!matchesTrade && tradeName"
        class="notice"
        data-test="manual-off-trade"
      >
        Cette annonce ne parle pas de « {{ tradeName }} » : la note dira si elle te correspond.
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
      >
        <input
          :id="id"
          v-model="draft.company"
          maxlength="300"
          autocomplete="organization"
          type="text"
          :aria-describedby="describedby"
          :aria-invalid="invalid"
          data-test="manual-company"
        >
      </FormField>
      <div class="manual-read-pair">
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Lieu"
        >
          <input
            :id="id"
            v-model="draft.location"
            maxlength="300"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="manual-location"
          >
        </FormField>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Contrat"
        >
          <input
            :id="id"
            v-model="draft.contract"
            maxlength="100"
            type="text"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="manual-contract"
          >
        </FormField>
      </div>
      <div class="manual-text">
        <button
          type="button"
          class="manual-text-row"
          :aria-expanded="textOpen"
          :aria-controls="`${formId ?? 'manual'}-text`"
          data-test="manual-text-toggle"
          @click="textOpen = !textOpen"
        >
          <AppIcon name="file" />
          <span class="manual-text-what">
            <strong>{{ readBy === "main" ? "Texte de l’annonce" : "Texte lu" }}</strong>
            <span data-test="manual-text-line">{{ textLine }}</span>
          </span>
          <AppIcon
            name="chevron-down"
            :class="{ turned: textOpen }"
          />
        </button>
        <div
          v-show="textOpen"
          :id="`${formId ?? 'manual'}-text`"
          class="manual-text-body"
        >
          <textarea
            v-model="draft.description"
            rows="8"
            maxlength="20000"
            aria-label="Texte de l’annonce"
            data-test="manual-description"
          />
          <p class="hint">
            Il sert à la note, à la lettre et au CV adapté.
          </p>
        </div>
      </div>
      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
    </section>
  </form>
</template>

<style scoped>
.manual-form { --manual-13: 13px; --manual-6: 6px; --manual-pad: var(--panel-pad-x, var(--sheet-pad, var(--space-6))); }
/* Planche CandidaturesOrdinateurAjouter du 13.11 : la zone de 3 lignes (104 px ; le champ commun la ramenait à 56) ;
   le compte 6 px dessous ; « Importer le PDF de l'annonce » en pilule de 44 px, 20 px sous le compte. */
.form-field-box .manual-entry { --manual-104: 104px; min-height: var(--manual-104); }
.manual-pdf { --manual-18: 18px; justify-self: start; gap: var(--space-2); min-height: var(--target-min); padding: 0 var(--manual-18); border-radius: var(--radius-pill); font-size: var(--font-label); }
.manual-form > .form-field + [data-test="manual-count"] { margin-top: calc(var(--manual-6) - var(--space-4)); }
.manual-form > .manual-pdf { margin-top: var(--space-1); }
.manual-read { display: grid; gap: var(--space-4); }
.manual-read-cap { margin: var(--space-2) 0 0; color: var(--muted); font-size: var(--manual-13); font-weight: var(--weight-bold); letter-spacing: 0.08em; text-transform: uppercase; }
.manual-read-pair { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.manual-text { margin: 0 calc(-1 * var(--manual-pad)); border-block: 1px solid var(--line); }
.manual-text-row { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: var(--target-min); padding: var(--space-3) var(--manual-pad); border: 0; border-radius: 0; background: none; color: inherit; font: inherit; text-align: left; cursor: pointer; }
@media (hover: hover) { .manual-text-row:hover { background: var(--primary-soft); } }
.manual-text-what { display: grid; flex: 1; min-width: 0; }
.manual-text-what span { color: var(--muted); font-size: var(--manual-13); }
.manual-text-row .turned { transform: rotate(180deg); }
.manual-text-body { display: grid; gap: var(--space-2); padding: 0 var(--manual-pad) var(--space-4); }
.manual-text-body .hint { margin: 0; }
.manual-text-body textarea { --manual-240: 240px; --manual-12: 12px; height: var(--manual-240); border-radius: var(--manual-12); field-sizing: fixed; overflow: auto; }
</style>
