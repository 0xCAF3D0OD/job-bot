<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, useId } from "vue";

import { api } from "../api/client";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";
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
  added: [result: { id: number; existing: boolean; status: string; reasons: string[]; filled?: string[]; filled_values?: Record<string, string> }];
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
// Déjà là (décision de Kevin du 16.11, retour sur la #818) : un message sous le champ, puis ses boutons, à la place
// d'« Ajouter l'offre ». Même lien : « Ouvrir l'offre » seul. Même poste chez la même entreprise, lien différent :
// « Ouvrir l'offre » et « Ajouter quand même ». Ouvrir ajoute à l'offre déjà là le lien et les champs vides que cette
// annonce remplit, sans rien remplacer (demande de Kevin, 2026-11-05).
const existingKind = ref<"link" | "post" | null>(null);
const existingTitle = ref("");
const existingCompany = ref("");
const existingAdded = ref<string | null>(null);
// Les champs vides de l'offre déjà là que cette annonce remplit : « Ouvrir l'offre » les ajoute (Kevin, 17.11).
const fillable = ref<string[]>([]);
const duplicate = computed(() => shown.value && existingId.value !== null && existingKind.value !== null);
const duplicateText = computed(() => {
  const added = existingAdded.value ? `ajoutée ${dateInSentence(existingAdded.value)}` : "";
  if (existingKind.value === "link") return `Cette offre est déjà dans tes candidatures${added ? ` (${added})` : ""}.`;
  const at = existingCompany.value ? ` chez ${existingCompany.value}` : "";
  return `Une offre très proche est déjà là : ${existingTitle.value}${at}${added ? `, ${added}` : ""}.`;
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
const low = computed(() => left.value <= 5);
const helpId = useId();
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
    existingKind.value = d.existing_kind ?? (existingId.value !== null ? "post" : null);
    existingTitle.value = d.existing_title ?? "";
    existingCompany.value = d.existing_company ?? "";
    existingAdded.value = d.existing_added ?? null;
    fillable.value = d.fillable ?? [];
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
  existingKind.value = null;
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

// « Capture ou PDF » : son texte, lu par le serveur, arrive dans le champ ; la personne le relit, puis ajoute.
const picker = ref<HTMLInputElement | null>(null);
const importing = ref(false);
const pdfProblem = ref("");
const pdfDone = ref(false);
function pickPdf(): void {
  if (importing.value || full.value) return;
  picker.value?.click();
}
async function importPdf(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || importing.value) return;
  pdfProblem.value = "";
  pdfDone.value = false;
  await importFile(file);
}

// Planche AjouterOffreTel (§72d du 18.11), téléphone et ordinateur (Kevin, 18.11, 16 h 21 : même contenu partout) :
// « Capture ou PDF » lit un PDF sans IA ou une capture PNG ou JPG par l'IA, avec la règle de la fiche (Q1 du 17.11 : 5 Mo, 20 par heure, la capture compte dans la formule). Le texte
// arrive dans le champ, à relire avant « Ajouter l'offre ». La lecture est chargée au premier fichier (offerFile.ts).
async function importFile(file: File): Promise<void> {
  importing.value = true;
  try {
    const { readManualFile } = await import("../offerFile");
    const found = await readManualFile(file);
    if (found.text) {
      entry.value = found.text;
      mode.value = "text";
      entryChanged();
      problem.value = "";
      pdfDone.value = true;
    } else pdfProblem.value = found.error ?? "Import impossible pour l’instant : réessaie.";
  } catch {
    pdfProblem.value = "Import impossible pour l’instant : réessaie.";
  } finally {
    importing.value = false;
  }
}

// « Coller » (Kevin, 18.11 ; planche AjouterOffreTel) : le presse-papiers, lu sur ce toucher seulement, avec la demande
// d'autorisation du système, arrive dans le champ. Accès refusé ou presse-papiers vide : le curseur va dans le champ,
// où l'on colle à la main.
const form = ref<HTMLFormElement | null>(null);
// Les deux boutons de la barre du champ ; leurs icônes, dessinées par la planche, restent dans le gabarit (dans
// icons.ts, elles pèseraient sur toutes les pages).
const TOOLS = [
  { id: "paste", label: "Coller" },
  { id: "file", label: "Capture ou PDF" },
] as const;
async function pasteClipboard(): Promise<void> {
  let copied = "";
  try {
    copied = (await navigator.clipboard?.readText?.())?.trim() ?? "";
  } catch {
    copied = "";
  }
  if (copied) {
    entry.value = copied;
    entryChanged();
  }
  await nextTick();
  form.value?.querySelector("textarea")?.focus();
}

const separating = ref(false);
function open(): void {
  separating.value = false;
  void add(null);
}
function addAnyway(): void {
  separating.value = true;
  void add(null, true);
}

async function submit(event: Event): Promise<void> {
  if (reading.value || saving.value || importing.value || duplicate.value) return;
  if (shown.value) await add(event);
  else if (!full.value) await read();
}

async function add(event: Event | null, separate = false): Promise<void> {
  if (event && !(await valid(event.currentTarget, "title"))) return;
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
        // Déjà là (décision de Kevin du 16.11) : la fiche existante s'ouvre, avec le lien et les champs vides que cette
        // annonce remplit ; « Ajouter quand même » (doublon probable) en fait une offre à part.
        fill: existingId.value !== null && !separate,
        separate,
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

// Maquette du 8 novembre (LISEZMOI, Composer) : 3 lignes sur ordinateur, 4 sur téléphone (AjouterOffreTel).
const { phone } = usePhone();

// Le bouton du pied du panneau (OffersView) : son libellé et son attente.
defineExpose({
  shown,
  full,
  duplicate,
  busy: computed(() => reading.value || saving.value),
  label: computed(() => "Ajouter l’offre"),
  busyLabel: computed(() => (reading.value ? "Lecture de l’annonce…" : "Ajout…")),
});
</script>

<template>
  <form
    :id="formId"
    ref="form"
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
      :describedby="helpId"
      data-test="manual-entry"
      @update:model-value="entryChanged"
      @send="read"
    >
      <!-- Planche AjouterOffreTel (§72d du 18.11) : « Coller » et « Capture ou PDF » dans la barre du champ, à gauche de
           la flèche ; boutons texte bleus de 44 px, icône et texte, sans fond. -->
      <template #tools>
        <button
          v-for="tool in TOOLS"
          :key="tool.id"
          type="button"
          class="manual-tool"
          :aria-disabled="tool.id === 'file' && (importing || full) ? 'true' : undefined"
          :data-test="`manual-${tool.id}`"
          @click="tool.id === 'paste' ? pasteClipboard() : pickPdf()"
        >
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          ><template v-if="tool.id === 'paste'"><rect
            x="6"
            y="4"
            width="12"
            height="17"
            rx="2"
          /><path d="M9 4V3h6v1" /></template><template v-else><rect
            x="4"
            y="5"
            width="16"
            height="14"
            rx="2"
          /><circle
            cx="9"
            cy="10"
            r="1.5"
          /><path d="m20 16-5-5-8 8" /></template></svg>{{ tool.label }}
        </button>
      </template>
    </Composer>
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
    <!-- Ordinateur (Kevin, 18.11, 16 h 21) : les mêmes « Coller » et « Capture ou PDF », sous le champ, alignés à droite
         comme dans la barre du champ du téléphone ; ils remplacent « Importer le PDF de l’annonce ». -->
    <div
      v-if="!phone && !shown"
      class="manual-desk-tools"
    >
      <button
        v-for="tool in TOOLS"
        :key="tool.id"
        type="button"
        class="manual-tool"
        :aria-disabled="tool.id === 'file' && (importing || full) ? 'true' : undefined"
        :data-test="`manual-${tool.id}`"
        @click="tool.id === 'paste' ? pasteClipboard() : pickPdf()"
      >
        <svg
          class="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        ><template v-if="tool.id === 'paste'"><rect
          x="6"
          y="4"
          width="12"
          height="17"
          rx="2"
        /><path d="M9 4V3h6v1" /></template><template v-else><rect
          x="4"
          y="5"
          width="16"
          height="14"
          rx="2"
        /><circle
          cx="9"
          cy="10"
          r="1.5"
        /><path d="m20 16-5-5-8 8" /></template></svg>{{ tool.label }}
      </button>
    </div>
    <p
      v-if="phone && entryError"
      class="field-error"
      role="alert"
      data-test="manual-entry-error"
    >
      {{ entryError }}
    </p>
    <template v-if="duplicate">
      <p
        class="manual-duplicate"
        role="alert"
        data-test="manual-existing"
      >
        <AppIcon name="info" />
        <span>
          {{ duplicateText }}
          <template v-if="fillable.length">
            <br><span data-test="manual-fillable">Ouvrir l’offre complète aussi les informations qui lui manquent.</span>
          </template>
        </span>
      </p>
      <div class="manual-duplicate-actions">
        <BusyButton
          type="button"
          class="primary"
          :busy="saving && !separating"
          busy-label="Ouverture…"
          :disabled="saving"
          data-test="manual-open-existing"
          @click="open"
        >
          Ouvrir l’offre
        </BusyButton>
        <BusyButton
          v-if="existingKind === 'post'"
          type="button"
          class="secondary"
          :busy="saving && separating"
          busy-label="Ajout…"
          :disabled="saving || full"
          data-test="manual-separate"
          @click="addAnyway"
        >
          Ajouter quand même
        </BusyButton>
      </div>
    </template>
    <!-- Téléphone (planche AjouterOffreTel, §72 du 18.11) : les pastilles sous le champ, liées à lui : « Capture ou PDF :
         compte dans ta formule », puis, à 5 ajouts ou moins, la pastille orange du quota (§17 du 15 novembre).
         Ordinateur : la ligne du quota, comme avant. -->
    <div
      v-if="phone"
      :id="helpId"
      class="manual-pills"
      data-test="manual-help"
    >
      <span class="manual-pill">Capture ou PDF : compte dans ta formule</span>
      <span
        v-if="low"
        class="manual-quota"
        data-test="manual-count"
      >{{ full ? countLine : `Plus que ${left} ajout${left > 1 ? "s" : ""} aujourd’hui` }}</span>
    </div>
    <p
      v-else
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
      {{ importing ? "Lecture du fichier…" : "Lecture de l’annonce…" }}
    </p>
    <p
      v-else-if="pdfDone && !shown"
      class="hint"
      role="status"
      data-test="manual-pdf-done"
    >
      Texte du fichier repris. Relis-le, puis ajoute l’offre.
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
      accept="application/pdf,.pdf,image/png,image/jpeg"
      class="visually-hidden"
      tabindex="-1"
      aria-hidden="true"
      data-test="manual-pdf-file"
      @change="importPdf"
    >

    <p
      v-if="pdfProblem"
      class="notice"
      role="alert"
      data-test="manual-pdf-problem"
    >
      {{ pdfProblem }}
    </p>
    <section
      v-if="shown && !duplicate"
      class="manual-read"
      data-test="manual-draft"
    >
      <h3 class="manual-read-cap">
        {{ readBy === "main" ? "À remplir toi-même" : "Ce que jobA1 a lu" }}
      </h3>
      <p
        v-if="!matchesTrade && tradeName"
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
    </section>
    <p
      v-if="error && shown"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
  </form>
</template>

<style scoped>
.manual-form { --manual-13: 13px; --manual-pad: var(--panel-pad-x, var(--sheet-pad, var(--space-6))); }
.manual-entry { --manual-104: 104px; min-height: var(--manual-104); }
/* AjouterOffreTel : champ de 104 px (4 lignes de 24 et ses marges), aide 13 px 8 px dessous (10 sur la planche), quota en
   pastille orange (avertissement). */
.manual-form :deep(.composer textarea) { --manual-104: 104px; min-height: var(--manual-104); }
/* Planche AjouterOffreTel (§72d du 18.11) : boutons texte bleus de 44 px, icône 18 px et texte, sans fond ; pastilles de
   13 px sous le champ, 10 px plus bas, 8 px entre elles. */
.manual-tool { display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--target-min); padding: 0 var(--space-2); border: 0; border-radius: var(--radius-pill); background: none; color: var(--primary-text); font: inherit; font-size: var(--font-small); font-weight: var(--weight-bold); white-space: nowrap; cursor: pointer; }
.manual-tool .icon { flex: none; width: 18px; height: 18px; }
.manual-tool[aria-disabled="true"] { opacity: 0.6; cursor: not-allowed; }
@media (hover: hover) { .manual-tool:hover { background: var(--primary-soft); } }
.manual-desk-tools { display: flex; justify-content: flex-end; gap: var(--space-1); margin-top: calc(var(--space-1) - var(--space-4)); }
.manual-pills { --manual-10: 10px; --manual-5: 5px; display: flex; flex-wrap: wrap; gap: var(--space-2); margin: calc(var(--manual-10) - var(--space-4)) 0 0; }
.manual-pill, .manual-quota { display: inline-flex; padding: var(--manual-5) var(--space-3); border-radius: var(--radius-pill); font-size: var(--manual-13); font-weight: var(--weight-semibold); }
.manual-pill { background: var(--line-soft); color: var(--text-lead); }
.manual-quota { background: var(--warning-soft); color: var(--warning); }
/* Déjà là : le message sous le champ, icône et texte, puis ses boutons (retour de Kevin sur la #818). */
.manual-duplicate { display: flex; gap: var(--space-2); align-items: flex-start; margin: 0; font-size: var(--font-small); line-height: var(--leading-normal); font-weight: var(--weight-semibold); }
.manual-duplicate .icon { flex: none; width: 18px; height: 18px; margin-top: 1px; color: var(--text-secondary); }
.manual-duplicate-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }
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
