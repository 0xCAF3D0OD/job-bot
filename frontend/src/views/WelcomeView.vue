<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type CriteriaIn, type Offer, type SettingsModel } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import BrandMark from "../components/BrandMark.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import IconButton from "../components/IconButton.vue";
import ScoreRing from "../components/ScoreRing.vue";
import TagInput from "../components/TagInput.vue";
import { useAuth } from "../composables/useAuth";
import { rateText, remoteText } from "../format";
import { whyLine } from "../whyLine";

// Les premiers pas (maquette OnboardingC, docs/139 étape 11b ; O1 à O10, Kevin, 2026-11-05) : quatre étapes, une
// barre en quatre segments et « Passer » en haut.
// 1. La page bleue : « Moins chercher plus vivre. ».
// 2. Le CV : lu par l'IA quand elle est branchée (sans les coordonnées, llm/redact.py) ; ses compétences.
// 3. Les critères : postes en puces (pré-remplis par le CV), lieux en puces, l'ORP et ses recherches par mois.
// 4. Le tri : jusqu'à 3 offres déjà notées, à garder ou écarter ; sinon, directement « Tout est prêt. ».
// Ce qui n'est plus demandé prend une valeur par défaut (O1), rappelée en une ligne à la fin, modifiable dans
// Compte : taux peu importe, langues du CV (sinon le français), télétravail accepté, remise le 5, téléphone
// désactivé.
type Understanding = components["schemas"]["Understanding"];
type Step = 0 | 1 | 2 | 3;
const OTHER_LANGUAGES = ["allemand", "italien", "anglais"] as const;
const LANGUAGE_NAMES: Record<string, string> = { allemand: "allemand", italien: "italien", anglais: "anglais" };
const MAX_ROLES = 3;
const DUE_DAY = 5;
// Le gribouillis qui barre le premier mot de chaque titre : le tracé de la maquette (comme « C'est fait ! »).
const SCRIBBLE =
  "M2 22 10.3 3.9 14.3 34.2 18.8 6 25.4 31.4 32 8 37.6 34.8 43 5.4 46.3 36.2 51.3 3.7 58.9 32.1 65.3 5.2 69.4 31.4 76.8 5.6 83.5 33.7 91 7.2 97.9 34.2 104 4.7 107.5 33.5 111.6 5.9 119.2 35.6 126.6 4.9 132.6 34.5 140 8.7 146.7 31.4 152.9 9 157.4 33.3 161.2 5.8 166.3 31.4 170.3 4.5 178 31.5 184.3 8.3 191.1 32.7 196.7 8.3 198 32.1M196 14C150 30 90 6 40 26S8 18 4 30";
// Chaque titre : un début, le mot barré, la fin manuscrite (Caveat Brush, réduite à ces seuls caractères).
const TITLES: { lead: string; struck: string; hand: string }[] = [
  { lead: "Moins", struck: "chercher", hand: "plus vivre." },
  { lead: "", struck: "Tout réécrire", hand: "Ton CV suffit." },
  { lead: "", struck: "Toutes les offres", hand: "Juste les tiennes." },
  { lead: "Lire", struck: "312 offres", hand: "En trier 3." },
];

const router = useRouter();
const { me } = useAuth();

const step = ref<Step>(0);
const loaded = ref(false);
const criteria = ref<CriteriaIn | null>(null);
const settings = ref<SettingsModel | null>(null);

// Étape 2, le CV.
const cvName = ref("");
const cvId = ref<number | null>(null);
const uploading = ref(false);
const reading = ref(false);
const cvError = ref("");
const understanding = ref<Understanding | null>(null);
const skills = computed(() =>
  (understanding.value?.chunks ?? []).filter((c) => c.kind === "competence").map((c) => c.title).slice(0, 8),
);

// Étape 3, les critères.
const roles = ref<string[]>([]);
const picked = ref<string[]>([]);
const newRole = ref("");
const places = ref<string[]>([]);
const orp = ref(true);
const target = ref(10);

// Étape 4, le tri.
const offers = ref<Offer[]>([]);
const position = ref(0);
const kept = ref(0);
const dismissed = ref(0);
const deciding = ref(false);
const sorting = computed(() => step.value === 3 && position.value < offers.value.length);
const current = computed(() => offers.value[position.value] ?? null);

function focusTitle(el: Element): void {
  const title = el.querySelector<HTMLElement>("h1");
  if (!title) return;
  title.setAttribute("tabindex", "-1");
  title.focus({ preventScroll: true });
}

async function remember(changes: Record<string, unknown>): Promise<void> {
  await api.PUT("/api/welcome", { body: changes });
}

onMounted(async () => {
  const [state, found, saved] = await Promise.all([api.GET("/api/welcome"), api.GET("/api/criteria"), api.GET("/api/settings")]);
  if (found.data) {
    criteria.value = found.data.criteria;
    places.value = [...(found.data.criteria.locations ?? [])];
  }
  if (saved.data) {
    settings.value = saved.data;
    if (saved.data.orp_monthly_target) target.value = saved.data.orp_monthly_target;
  }
  if (state.data) {
    roles.value = [...(state.data.roles ?? [])];
    picked.value = [...roles.value];
    if (state.data.goal === "job") orp.value = false;
    // Reprendre là où on s'était arrêté, sans revenir au tri (il se recharge à l'étape 3).
    if (state.data.status !== "done") step.value = Math.max(0, Math.min(state.data.step - 1, 2)) as Step;
  }
  loaded.value = true;
});

function go(next: Step): void {
  step.value = next;
  void remember({ step: next + 1 });
}

async function onCv(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  uploading.value = true;
  cvError.value = "";
  try {
    const { data, error } = await api.POST("/api/documents", {
      body: { file: "" },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    if (data) {
      cvName.value = data.filename;
      cvId.value = data.id;
      understanding.value = null;
      void understand(data.id);
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      cvError.value = typeof detail === "string" ? `Refusé : ${detail}.` : "Ce fichier n'a pas pu être importé.";
    }
  } finally {
    uploading.value = false;
  }
}

// Le CV lu par l'IA (docs/121 §A), sans les coordonnées. Sans IA, plafond atteint ou erreur : pas de
// compétences, et l'étape 3 part de ce qui est déjà enregistré.
async function understand(documentId: number): Promise<void> {
  reading.value = true;
  try {
    const { data } = await api.POST("/api/documents/{document_id}/understand", { params: { path: { document_id: documentId } } });
    if (!data || (!data.chunks.length && !data.roles.length)) return;
    understanding.value = data;
    const known = new Set(roles.value.map((r) => r.toLowerCase()));
    const found = data.roles.filter((r) => !known.has(r.toLowerCase()));
    roles.value = [...roles.value, ...found];
    picked.value = [...picked.value, ...found].slice(0, MAX_ROLES);
  } catch {
    understanding.value = null;
  } finally {
    reading.value = false;
  }
}

// « Continuer » : les blocs lus dans le CV (sauf ceux déjà dans le profil) rejoignent le profil, rattachés au
// CV ; ils restent modifiables dans Profil.
function confirmCv(): void {
  const found = understanding.value;
  go(2);
  if (!found) return;
  for (const chunk of found.chunks.filter((c) => c.duplicate_of == null)) {
    void api.POST("/api/profile-chunks", {
      body: { kind: chunk.kind, title: chunk.title, content: chunk.content, tags: chunk.tags, active: true, document_id: cvId.value },
    });
  }
}

function toggleRole(role: string): void {
  if (picked.value.includes(role)) picked.value = picked.value.filter((r) => r !== role);
  else if (picked.value.length < MAX_ROLES) picked.value = [...picked.value, role];
}

function addRole(): void {
  const role = newRole.value.trim().slice(0, 80);
  newRole.value = "";
  if (!role) return;
  if (!roles.value.some((r) => r.toLowerCase() === role.toLowerCase())) roles.value = [...roles.value, role];
  const same = roles.value.find((r) => r.toLowerCase() === role.toLowerCase())!;
  if (!picked.value.includes(same) && picked.value.length < MAX_ROLES) picked.value = [...picked.value, same];
}

// Les langues : celles que le CV mentionne, sinon le français seul.
const spoken = computed(() => (understanding.value?.languages ?? []).filter((l) => (OTHER_LANGUAGES as readonly string[]).includes(l)));

// « Voir mes offres » : les critères, les réglages et les postes partent ensemble, avec les valeurs par défaut.
async function confirmCriteria(): Promise<void> {
  if (criteria.value) {
    criteria.value = {
      ...criteria.value,
      locations: places.value,
      min_rate: null,
      remote_policy: "from_switzerland",
      unspoken_languages: OTHER_LANGUAGES.filter((l) => !spoken.value.includes(l)),
    };
    void api.PUT("/api/criteria", { body: criteria.value });
  }
  if (settings.value) {
    settings.value = { ...settings.value, orp_monthly_target: orp.value ? target.value : null, orp_due_day: DUE_DAY };
    void api.PUT("/api/settings", { body: settings.value });
  }
  step.value = 3;
  void remember({ step: 4, goal: orp.value ? "orp" : "job", roles: picked.value, ...(picked.value[0] ? { trade: picked.value[0] } : {}) });
  const { data } = await api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 3 } } });
  offers.value = (data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined).slice(0, 3);
}

// « Garder » et « Écarter » : comme dans Candidatures.
async function decide(choice: "keep" | "dismiss"): Promise<void> {
  const offer = current.value;
  if (!offer || deciding.value) return;
  deciding.value = true;
  try {
    const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
      params: { path: { offer_id: offer.id } },
      body: { status: choice === "keep" ? "preparing" : "ignored" },
    });
    if (!response.ok) return;
    if (choice === "keep") kept.value += 1;
    else dismissed.value += 1;
    position.value += 1;
  } finally {
    deciding.value = false;
  }
}

const tags = computed(() => {
  const o = current.value;
  if (!o) return [];
  return [rateText(o.rate_min, o.rate_max).replace("–", " à "), o.employment_type ?? "", remoteText(o) ?? ""].filter(Boolean).slice(0, 3);
});

const sortSummary = computed(() => {
  const parts = [
    kept.value ? `${kept.value} ${kept.value === 1 ? "offre gardée" : "offres gardées"}` : "",
    dismissed.value ? `${dismissed.value} ${dismissed.value === 1 ? "écartée" : "écartées"}` : "",
  ].filter(Boolean);
  if (!offers.value.length) return "Tes premières offres arrivent après la prochaine collecte.";
  return parts.length ? `${parts.join(", ")}.` : "";
});
// Les valeurs par défaut (O1), en une ligne.
const defaults = computed(() =>
  [
    "Taux : peu importe",
    `Langues : ${["français", ...spoken.value.map((l) => LANGUAGE_NAMES[l])].join(", ")}`,
    "Télétravail : accepté",
    ...(orp.value ? [`Remise ORP : le ${DUE_DAY}`] : []),
    "Téléphone : désactivé",
  ].join(" · "),
);

async function later(): Promise<void> {
  await remember({ postponed: true });
  if (me.value) me.value = { ...me.value, welcome: "postponed" };
  await router.replace("/aujourdhui");
}

async function finish(to: string): Promise<void> {
  await remember({ done: true, postponed: false });
  if (me.value) me.value = { ...me.value, welcome: "done" };
  await router.replace(to);
}
</script>

<template>
  <section
    v-if="loaded"
    :class="['welcome', { 'welcome-blue': step === 0 }]"
    data-test="welcome"
  >
    <div class="welcome-column">
      <header class="welcome-top">
        <IconButton
          v-if="step > 0"
          icon="arrow-left"
          label="Étape précédente"
          data-test="welcome-back"
          @click="go((step - 1) as Step)"
        />
        <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
        <button
          v-if="!(step === 3 && !sorting)"
          type="button"
          class="link welcome-later"
          data-test="welcome-later"
          @click="later"
        >
          Passer
        </button>
      </header>
      <div
        class="welcome-progress"
        role="progressbar"
        :aria-label="`Étape ${step + 1} sur 4`"
        aria-valuemin="1"
        aria-valuemax="4"
        :aria-valuenow="step + 1"
      >
        <span
          v-for="i in 4"
          :key="i"
          :class="{ done: i <= step + 1 }"
        />
      </div>

      <Transition
        name="welcome-step"
        mode="out-in"
        @after-enter="focusTitle"
      >
        <div
          :key="step"
          class="welcome-screen"
          :data-test="`welcome-step-${step + 1}`"
        >
          <h1 class="welcome-title">
            <template v-if="TITLES[step]!.lead">
              {{ `${TITLES[step]!.lead} ` }}
            </template>
            <span class="welcome-struck"><s>{{ TITLES[step]!.struck }}</s><svg
              viewBox="0 0 200 40"
              preserveAspectRatio="none"
              aria-hidden="true"
            ><path
              :d="SCRIBBLE"
              pathLength="1"
            /></svg></span>{{ " " }}<br>
            <span class="welcome-hand">{{ TITLES[step]!.hand }}</span>
          </h1>

          <template v-if="step === 0">
            <p class="welcome-lead">
              jobA1 trie les offres, prépare tes lettres et tient ton suivi ORP. En 3 étapes, on règle tout.
            </p>
          </template>

          <template v-else-if="step === 1">
            <p class="welcome-lead">
              jobA1 en tire tes compétences pour noter chaque offre.
            </p>
            <div
              v-if="cvName"
              class="welcome-cv"
              role="status"
              data-test="cv-done"
            >
              <div class="welcome-cv-file">
                <span class="welcome-cv-check"><AppIcon name="check" /></span>
                <span>
                  <strong>{{ cvName }}</strong>
                  <small data-test="cv-reading">{{ reading ? "Lecture de ton CV…" : understanding ? "Importé et analysé" : "Importé" }}</small>
                </span>
                <label class="link welcome-cv-change">
                  Changer
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    class="visually-hidden"
                    @change="onCv"
                  >
                </label>
              </div>
              <div
                v-if="skills.length"
                class="welcome-skills"
                data-test="cv-skills"
              >
                <p>Compétences trouvées</p>
                <ul>
                  <li
                    v-for="skill in skills"
                    :key="skill"
                  >
                    {{ skill }}
                  </li>
                </ul>
              </div>
            </div>
            <label
              v-else
              class="welcome-drop"
              data-test="cv-upload"
            >
              <strong>Importer mon CV</strong>
              <small>PDF ou Word, 10 Mo maximum</small>
              <span class="welcome-drop-button">{{ uploading ? "Import…" : "Choisir un fichier" }}</span>
              <input
                type="file"
                accept=".pdf,.docx"
                class="visually-hidden"
                @change="onCv"
              >
            </label>
            <p
              v-if="cvError"
              class="notice"
              role="alert"
            >
              {{ cvError }}
            </p>
            <p
              class="welcome-privacy"
              data-test="cv-privacy"
            >
              <AppIcon name="lock" />
              <span>Ton CV reste privé : il sert à noter les offres et à préparer tes lettres. L'IA n'en reçoit que les parties utiles,
                sans tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
            </p>
          </template>

          <template v-else-if="step === 2">
            <p class="welcome-lead">
              Pré-rempli depuis ton CV. Modifiable à tout moment dans Compte.
            </p>
            <fieldset class="welcome-field">
              <legend>Postes</legend>
              <div
                class="welcome-roles"
                data-test="roles"
              >
                <button
                  v-for="role in roles"
                  :key="role"
                  type="button"
                  :class="['chip', 'welcome-role', { on: picked.includes(role) }]"
                  :aria-pressed="picked.includes(role)"
                  :aria-disabled="!picked.includes(role) && picked.length >= MAX_ROLES ? 'true' : undefined"
                  @click="toggleRole(role)"
                >
                  <AppIcon
                    v-if="picked.includes(role)"
                    name="check"
                  />{{ role }}
                </button>
              </div>
              <div class="tag-add">
                <input
                  id="welcome-role"
                  v-model="newRole"
                  type="text"
                  maxlength="80"
                  placeholder="Ajouter un poste"
                  aria-label="Ajouter un poste"
                  data-test="role-input"
                  @keydown.enter.prevent="addRole"
                >
                <IconButton
                  icon="plus"
                  label="Ajouter"
                  data-test="role-add"
                  @click="addRole"
                />
              </div>
              <p
                v-if="picked.length >= MAX_ROLES"
                class="welcome-note"
              >
                Trois postes au plus.
              </p>
            </fieldset>
            <div class="welcome-field">
              <label
                for="welcome-place"
                class="welcome-label"
              >Lieux</label>
              <TagInput
                id="welcome-place"
                v-model="places"
                placeholder="Une ville ou un canton"
              />
            </div>
            <div class="welcome-orp">
              <label class="welcome-orp-row">
                <span><strong>Je suis inscrit à l'ORP</strong><small>Active le suivi de tes recherches</small></span>
                <input
                  v-model="orp"
                  type="checkbox"
                  role="switch"
                  data-test="orp-switch"
                >
              </label>
              <div
                v-if="orp"
                class="welcome-orp-row"
              >
                <span id="welcome-target"><strong>Recherches par mois</strong></span>
                <button
                  type="button"
                  class="icon-button welcome-stepper"
                  aria-label="Moins"
                  data-test="target-minus"
                  @click="target = Math.max(1, target - 1)"
                >
                  −
                </button>
                <output
                  aria-live="polite"
                  aria-labelledby="welcome-target"
                  data-test="target"
                >{{ target }}</output>
                <button
                  type="button"
                  class="icon-button welcome-stepper"
                  aria-label="Plus"
                  data-test="target-plus"
                  @click="target = Math.min(30, target + 1)"
                >
                  +
                </button>
              </div>
            </div>
          </template>

          <template v-else>
            <template v-if="sorting && current">
              <p class="welcome-lead">
                Garde ou écarte. Celles que tu gardes t'attendent dans Candidatures.
              </p>
              <article
                :key="current.id"
                class="welcome-offer"
                data-test="welcome-offer"
              >
                <div class="welcome-offer-head">
                  <CompanyLogo :offer="current" />
                  <ScoreRing
                    :score="current.score ?? null"
                    worded
                  />
                </div>
                <p class="welcome-offer-title">
                  <strong>{{ current.title }}</strong>
                  <span>{{ [current.company || "Entreprise non indiquée", current.location].filter(Boolean).join(" · ") }}</span>
                </p>
                <ul
                  v-if="tags.length"
                  class="pick-tags"
                >
                  <li
                    v-for="tag in tags"
                    :key="tag"
                  >
                    {{ tag }}
                  </li>
                </ul>
                <p
                  v-if="current.why"
                  class="welcome-offer-why"
                >
                  <strong>D'après ton CV :</strong> {{ whyLine(current.why) }}
                </p>
              </article>
              <p
                class="welcome-count"
                aria-live="polite"
              >
                Offre {{ position + 1 }} sur {{ offers.length }}
              </p>
            </template>
            <div
              v-else
              class="welcome-ready"
              role="status"
              data-test="welcome-ready"
            >
              <span class="welcome-ready-check"><AppIcon name="check" /></span>
              <strong>Tout est prêt.</strong>
              <p
                v-if="sortSummary"
                data-test="welcome-sorted"
              >
                {{ sortSummary }}
              </p>
              <p
                class="welcome-defaults"
                data-test="welcome-defaults"
              >
                {{ defaults }}
              </p>
              <button
                type="button"
                class="link"
                data-test="welcome-account"
                @click="finish('/compte')"
              >
                Modifier dans Compte
              </button>
            </div>
          </template>
        </div>
      </Transition>

      <footer class="welcome-actions">
        <button
          v-if="step === 0"
          type="button"
          class="welcome-cta welcome-start"
          data-test="welcome-start"
          @click="go(1)"
        >
          C'est parti<AppIcon name="arrow-right" />
        </button>
        <button
          v-else-if="step === 1"
          type="button"
          class="primary welcome-cta"
          :disabled="uploading || reading"
          data-test="welcome-continue"
          @click="confirmCv"
        >
          {{ cvName ? "Continuer" : "Continuer sans CV" }}<AppIcon name="arrow-right" />
        </button>
        <button
          v-else-if="step === 2"
          type="button"
          class="primary welcome-cta"
          data-test="welcome-continue"
          @click="confirmCriteria"
        >
          Voir mes offres<AppIcon name="arrow-right" />
        </button>
        <div
          v-else-if="sorting"
          class="welcome-sort"
        >
          <button
            type="button"
            class="secondary"
            :aria-disabled="deciding ? 'true' : undefined"
            data-test="welcome-dismiss"
            @click="decide('dismiss')"
          >
            <AppIcon name="x-circle" />Écarter
          </button>
          <button
            type="button"
            class="primary"
            :aria-disabled="deciding ? 'true' : undefined"
            data-test="welcome-keep"
            @click="decide('keep')"
          >
            <AppIcon name="done" />Garder
          </button>
        </div>
        <button
          v-else
          type="button"
          class="primary welcome-cta"
          data-test="welcome-finish"
          @click="finish('/aujourdhui')"
        >
          Voir mes offres<AppIcon name="arrow-right" />
        </button>
      </footer>
    </div>
  </section>
</template>
