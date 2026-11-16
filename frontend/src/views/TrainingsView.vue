<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type Training } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import BusyButton from "../components/BusyButton.vue";
import DomainField from "../components/DomainField.vue";
import EmptyState from "../components/EmptyState.vue";
import HoverNote from "../components/HoverNote.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PushTransition from "../components/PushTransition.vue";
import SidePanel from "../components/SidePanel.vue";
import TrainingCardBody, { type MarkExtra } from "../components/TrainingCardBody.vue";
import TrainingModules from "../components/TrainingModules.vue";
import TrainingRow from "../components/TrainingRow.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { plural } from "../format";
import { FUNDING, ORP_LINKS, SHORT_FORMATS, progressLabel } from "../trainingLabels";

const { aiNote } = usePlan();
// Bilan › Formations (docs/16 §5 ; maquette Explorer, onglet Formations ; B15 à B19, Kevin, 2026-11-04).
// Catalogue : l'encadré du financement, les puces de filtre, les formations en lignes groupées, puis
// « Chercher d'autres formations ». Suivies : les formations en cours, puis les gardées et les terminées.
type Status = "interested" | "in_progress" | "done";
type Kind = "all" | "cert" | "cours";

const route = useRoute();
const { phone } = usePhone();
// Ordinateur (planche BilanOrdinateur, état Formations ; décision de Kevin du 2026-11-14) : d'abord la carte
// de l'ORP, « En cours » et « Gardées » ; le catalogue et ses filtres, inchangés, derrière « Chercher d'autres
// formations » (`?onglet=catalogue`).
// Téléphone comme ordinateur (§37 du 16.11, accord de Kevin à 14 h 06) : « Mes formations » d'abord, le catalogue
// derrière « Voir le catalogue » (`?onglet=catalogue`) et « ← Mes formations ». L'ancienne adresse `?onglet=miennes`
// mène aussi à « Mes formations ».
const tab = computed<"catalog" | "mine">(() => (route.query.onglet === "catalogue" ? "catalog" : "mine"));
const overview = computed(() => tab.value === "mine");
const catalogTo = { query: { onglet: "catalogue" } };
const mineTo = { query: {} };
const items = ref<Training[]>([]);
const keywords = ref<string[]>([]);
const canSuggest = ref(false);
const loaded = ref(false);
usePageReady("trainings", () => loaded.value);
const domainOnly = ref(true);
const suggesting = ref(false);
const message = ref("");

const hasDomain = computed(() => keywords.value.length > 0);
// Le catalogue vérifié n'a rien pour « Mon domaine », avant tout filtre (Kevin, 16.11).
const domainEmpty = computed(() => loaded.value && hasDomain.value && domainOnly.value && !items.value.length);

// Les puces (B17) : Tout, Certifications ou Cours, un seul choix ; « Gratuites » et « En français » s'ajoutent.
const kind = ref<Kind>("all");
const free = ref(false);
const french = ref(false);
const KIND_CHIPS: { key: Kind; label: string }[] = [
  { key: "all", label: "Tout" },
  { key: "cert", label: "Certifications" },
  { key: "cours", label: "Cours" },
];
const filtered = computed(() =>
  items.value.filter(
    (t) =>
      (kind.value === "all" || (kind.value === "cert") === (t.kind === "certification")) &&
      (!free.value || t.price === "free") &&
      (!french.value || t.language === "fr"),
  ),
);
// Deux groupes titrés avec leur nombre (B18) : « Certifications · 9 », « Cours et ateliers · 12 ».
const sections = computed(() =>
  [
    { key: "certifications", label: "Certifications", items: filtered.value.filter((t) => t.kind === "certification") },
    { key: "courses", label: "Cours et ateliers", items: filtered.value.filter((t) => t.kind !== "certification") },
  ].filter((section) => section.items.length),
);
// Suivies (B19) : en cours d'abord, en cartes ; puis les gardées et les terminées, en lignes.
const marked = computed(() => items.value.filter((t) => t.mark));
// Une carte : en cours, ou gardée avec son nombre de modules (le + du premier module la passe « en cours »).
const current = (t: Training): boolean =>
  t.mark!.status === "in_progress" || (t.mark!.status === "interested" && Boolean(t.mark!.modules_total));
const inProgress = computed(() => marked.value.filter(current));
const others = computed(() =>
  [
    ...marked.value.filter((t) => t.mark!.status === "interested" && !current(t)),
    ...marked.value.filter((t) => t.mark!.status === "done"),
  ],
);
const mineCount = computed(() => marked.value.length);
// Une gardée sur ordinateur : « éditeur · format · durée · gratuit », puis, à droite, où en est le
// financement ou « Terminée » (la planche dit « Financement possible » : aucune donnée ne le dit encore).
function keptMeta(t: Training): string {
  const format = SHORT_FORMATS[t.format] ?? t.format;
  return [t.provider, `${format.charAt(0).toUpperCase()}${format.slice(1)}`, t.duration, t.price === "free" ? "gratuit" : null]
    .filter(Boolean)
    .join(" · ");
}
function keptStatus(t: Training): { label: string; tone: string } | null {
  if (t.mark!.status === "done") return { label: "Terminée", tone: "done" };
  const funding = t.mark!.funding_status;
  return funding ? { label: FUNDING[funding] ?? funding, tone: funding } : null;
}

async function load(): Promise<void> {
  // Le catalogue de ton domaine quand il est connu ; sans domaine, tout le catalogue.
  const { data } = await api.GET("/api/trainings", {
    params: { query: { domain_only: domainOnly.value && (!loaded.value || hasDomain.value) } },
  });
  if (!data) return;
  items.value = data.items;
  keywords.value = data.domain_keywords;
  canSuggest.value = data.can_suggest;
  const first = !loaded.value;
  loaded.value = true;
  if (first && !data.domain_keywords.length && domainOnly.value) {
    domainOnly.value = false;
    await load();
  }
}

// Sans domaine, « Chercher d'autres formations » ouvre le champ du domaine sur place (docs/43 n° 4).
const domainFieldOpen = ref(false);
function onDomainSaved(): void {
  domainFieldOpen.value = false;
  domainOnly.value = true;
  void load();
}

function replace(training: Training): void {
  items.value = items.value.map((t) => (t.id === training.id ? training : t));
}

async function mark(
  training: Training,
  status: Status | null,
  extra: MarkExtra = {},
): Promise<void> {
  if (status === null) {
    await api.DELETE("/api/trainings/{training_id}/mark", { params: { path: { training_id: training.id } } });
    replace({ ...training, mark: null });
    return;
  }
  const { data } = await api.PUT("/api/trainings/{training_id}/mark", {
    params: { path: { training_id: training.id } },
    body: {
      status,
      progress: extra.progress ?? training.mark?.progress ?? null,
      done_at: extra.done_at ?? training.mark?.done_at ?? (status === "done" ? new Date().toISOString().slice(0, 10) : null),
      certified: extra.certified ?? training.mark?.certified ?? null,
      // B19 : un nombre de modules effacé (null) l'est vraiment ; absent, il reste.
      modules_total: "modules_total" in extra ? extra.modules_total : (training.mark?.modules_total ?? null),
      modules_done: "modules_done" in extra ? extra.modules_done : (training.mark?.modules_done ?? null),
    },
  });
  if (data) replace({ ...training, mark: data });
}

// Le signet d'une ligne (docs/101) : garder (« Intéressé »), ou retirer cette seule marque.
async function toggleInterest(training: Training): Promise<void> {
  await mark(training, training.mark?.status === "interested" ? null : "interested");
}

async function review(training: Training, keep: boolean): Promise<void> {
  await api.POST("/api/trainings/{training_id}/review", {
    params: { path: { training_id: training.id } },
    body: { keep },
  });
  if (keep) replace({ ...training, verified: true });
  else items.value = items.value.filter((t) => t.id !== training.id);
}

async function suggest(): Promise<void> {
  // Bouton toujours actif (docs/29 §3) : sans domaine, il ouvre le champ du domaine.
  if (!hasDomain.value) {
    domainFieldOpen.value = true;
    message.value = "Indique d’abord ton domaine : les formations proposées en dépendent.";
    return;
  }
  suggesting.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/trainings/suggest");
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Recherche impossible : ${detail}.` : "Recherche impossible.";
      return;
    }
    message.value = data.added
      ? `${plural(data.added, "formation proposée, marquée", "formations proposées, marquées")} « à vérifier » : garde-les ou écarte-les.`
      : "Rien de nouveau trouvé cette fois.";
    await load();
  } finally {
    suggesting.value = false;
  }
}

// « Noter l'avancement » (§37 du 16.11, téléphone et ordinateur) : le compteur de modules quitte la carte pour une
// feuille du bas ; sans nombre de modules, le panneau de la formation, comme avant, pour écrire où on en est.
const progressId = ref<number | null>(null);
const progressOf = computed(() => items.value.find((t) => t.id === progressId.value) ?? null);
function noteProgress(training: Training): void {
  if (training.mark?.modules_total) progressId.value = training.id;
  else openId.value = training.id;
}

// Le financement (B16) : l'encadré ouvre la feuille « Formation et chômage ».
const fundingOpen = ref(false);

const openId = ref<number | null>(null);
// Une formation ouverte depuis l'aperçu de la capsule (docs/92) : `?formation=ID`.
watch(
  () => route.query.formation,
  (id) => {
    if (typeof id === "string" && Number(id)) openId.value = Number(id);
  },
  { immediate: true },
);
const opened = computed(() => items.value.find((t) => t.id === openId.value) ?? null);
// « Effacer les filtres » (règles §4, aucun résultat).
const activeFilters = computed(() => (kind.value !== "all" ? 1 : 0) + (free.value ? 1 : 0) + (french.value ? 1 : 0));
function clearFilters(): void {
  kind.value = "all";
  free.value = false;
  french.value = false;
}

onMounted(() => void load());
</script>

<template>
  <section class="band">
    <div :class="['container', 'trainings', { 'trainings-desk': !phone }]">
      <!-- Le catalogue revient par le lien « Mes formations » (planches BilanOrdinateurCatalogue et BilanCatalogue, 16.11). -->
      <RouterLink
        v-if="tab === 'catalog'"
        :to="mineTo"
        class="training-back"
        data-test="trainings-back"
      >
        <AppIcon name="arrow-left" />Mes formations
      </RouterLink>

      <LoadingBlocks
        v-if="!loaded"
        :heights="['4rem', '2.5rem', '20rem']"
      />
      <!-- Ordinateur (planche BilanOrdinateur, état Formations) : la carte de l'ORP, En cours, Gardées, puis le catalogue. -->
      <div
        v-else-if="overview"
        class="trainings-overview"
        data-test="trainings-overview"
      >
        <!-- Téléphone (planche BilanFormations) : toute la carte ouvre « Formation et chômage ». -->
        <button
          v-if="phone"
          type="button"
          class="training-orp-card"
          data-test="orp-note"
          @click="fundingOpen = true"
        >
          <span>
            <strong>L’ORP peut financer une formation</strong>
            <span>Avec l’accord de ta conseillère</span>
          </span>
          <span
            class="arrow-circle small"
            aria-hidden="true"
          ><AppIcon name="arrow-right" /></span>
        </button>
        <div
          v-else
          class="training-orp-card"
          data-test="training-orp-card"
        >
          <span>
            <strong>L’ORP peut financer une formation</strong>
            <span>Seulement avec l’accord préalable de ta conseillère, avant de t’inscrire.</span>
          </span>
          <button
            type="button"
            class="link training-orp-how"
            data-test="orp-note"
            @click="fundingOpen = true"
          >
            Comment demander<AppIcon name="chevron" />
          </button>
        </div>
        <!-- Aucune suivie (planche BilanOrdinateurFormVide, 16.11) : l'état vide commun et « Voir le catalogue ». -->
        <EmptyState
          v-if="!mineCount"
          title="Aucune formation suivie"
          scene="introuvable"
          :width="250"
          :desktop-width="260"
          :pill="phone ? 'Garde-en une avec son signet' : 'Garde une formation du catalogue avec son signet'"
          pill-icon="bookmark"
          data-test="trainings-none"
        >
          <template #actions>
            <RouterLink
              :to="catalogTo"
              class="button-link primary-link"
              data-test="trainings-none-catalog"
            >
              <AppIcon name="book" />Voir le catalogue
            </RouterLink>
          </template>
        </EmptyState>
        <section
          v-if="inProgress.length"
          class="training-block"
          aria-labelledby="trainings-current-h"
        >
          <div class="bilan-section-head">
            <h2 id="trainings-current-h">
              En cours
            </h2>
            <span>{{ plural(inProgress.length, "formation", "formations") }}</span>
          </div>
          <ul class="training-block-list">
            <li
              v-for="training in inProgress"
              :key="training.id"
              class="training-now"
              data-test="training-current"
            >
              <div class="training-now-head">
                <!-- Le titre ouvre le panneau de la formation (notes, financement, profil), qui reste accessible. -->
                <button
                  type="button"
                  class="training-now-open"
                  aria-haspopup="dialog"
                  data-test="training-now-open"
                  @click="openId = training.id"
                >
                  <strong>{{ training.title }}</strong>
                  <span>{{ training.provider }}</span>
                </button>
                <a
                  v-if="!phone"
                  :href="training.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="training-now-continue"
                  data-test="training-continue"
                >Continuer le cours<span class="visually-hidden"> (nouvel onglet)</span></a>
              </div>
              <TrainingModules
                v-if="training.mark!.modules_total"
                compact
                :title="training.title"
                :total="training.mark!.modules_total"
                :done="training.mark!.modules_done ?? 0"
                @save="(done) => mark(training, training.mark!.status, { modules_done: done })"
                @finish="(done) => mark(training, 'done', { modules_done: done })"
              />
              <p
                v-else
                class="training-current-progress"
              >
                {{ progressLabel(training.mark!) || "En cours" }}
              </p>
              <div class="training-now-actions">
                <button
                  type="button"
                  class="link training-now-update"
                  aria-haspopup="dialog"
                  data-test="training-update"
                  @click="noteProgress(training)"
                >
                  Noter l’avancement
                </button>
                <a
                  v-if="phone"
                  :href="training.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="training-now-continue"
                  data-test="training-continue"
                >Continuer le cours<span class="visually-hidden"> (nouvel onglet)</span></a>
              </div>
            </li>
          </ul>
        </section>
        <section
          v-if="others.length"
          class="training-block"
          aria-labelledby="trainings-kept-h"
        >
          <div class="bilan-section-head">
            <h2 id="trainings-kept-h">
              Gardées
            </h2>
            <span>{{ plural(others.length, "formation", "formations") }}</span>
          </div>
          <ul class="training-block-list">
            <li
              v-for="training in others"
              :key="training.id"
              data-test="training-kept"
            >
              <button
                type="button"
                class="training-kept-row"
                @click="openId = training.id"
              >
                <span class="training-kept-text">
                  <strong>{{ training.title }}</strong>
                  <span><span>{{ keptMeta(training) }}</span><span
                    v-if="phone && keptStatus(training)"
                    :class="['training-kept-status', keptStatus(training)!.tone]"
                    data-test="training-kept-status"
                  ><AppIcon
                    v-if="training.mark!.status === 'done'"
                    name="done"
                  />{{ keptStatus(training)!.label }}</span></span>
                </span>
                <span
                  v-if="!phone && keptStatus(training)"
                  :class="['training-kept-status', keptStatus(training)!.tone]"
                  data-test="training-kept-status"
                ><AppIcon
                  v-if="training.mark!.status === 'done'"
                  name="done"
                />{{ keptStatus(training)!.label }}</span>
                <span
                  class="arrow-circle small"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span>
              </button>
            </li>
          </ul>
        </section>
        <RouterLink
          v-if="mineCount"
          :to="catalogTo"
          class="training-more"
          data-test="trainings-catalog"
        >
          Chercher d’autres formations
        </RouterLink>
      </div>
      <template v-else-if="tab === 'catalog'">
        <!-- Le financement (B16) : un encadré pêche qui ouvre « Formation et chômage ». -->
        <button
          type="button"
          class="training-funding-note"
          data-test="orp-note"
          @click="fundingOpen = true"
        >
          <span
            class="training-funding-icon"
            aria-hidden="true"
          ><AppIcon name="tag" /></span>
          <span><strong>Financement possible par l’ORP</strong><span>{{ phone ? "Avec" : "Seulement avec" }} l’accord préalable de l’ORP</span></span>
          <span
            class="arrow-circle small"
            aria-hidden="true"
          ><AppIcon name="arrow-right" /></span>
        </button>
        <!-- Les puces (B17) : le genre, un seul choix ; « Gratuites » et « En français » s'ajoutent. -->
        <div
          class="training-chips"
          role="group"
          aria-label="Filtrer les formations"
        >
          <button
            v-for="chip in KIND_CHIPS"
            :key="chip.key"
            type="button"
            class="training-chip"
            :aria-pressed="kind === chip.key"
            :data-test="`chip-${chip.key}`"
            @click="kind = chip.key"
          >
            {{ chip.label }}
          </button>
          <span
            class="training-chips-sep"
            aria-hidden="true"
          />
          <button
            type="button"
            class="training-chip"
            :aria-pressed="free"
            data-test="chip-free"
            @click="free = !free"
          >
            Gratuites
          </button>
          <button
            type="button"
            class="training-chip"
            :aria-pressed="french"
            data-test="chip-fr"
            @click="french = !french"
          >
            En français
          </button>
        </div>
        <!-- Rien pour « Mon domaine » dans le catalogue vérifié (Kevin, 16.11) : l'état vide commun et la recherche
             web existante en bouton principal. La ligne grise reste pour les seuls filtres qui vident la liste. -->
        <EmptyState
          v-if="domainEmpty"
          :title="`Rien dans le catalogue pour ${keywords[0]}`"
          scene="introuvable"
          :desktop-width="260"
          pill="Le catalogue couvre surtout l’informatique pour l’instant"
          pill-icon="book"
          data-test="trainings-domain-empty"
        >
          <template
            v-if="canSuggest"
            #actions
          >
            <BusyButton
              class="primary"
              :busy="suggesting"
              busy-label="Recherche en cours…"
              data-test="suggest-domain"
              @click="suggest"
            >
              <HoverNote :text="suggesting ? '' : aiNote('Environ 0,02 à 0,05 $.')">
                <span class="with-icon"><AppIcon name="search" />Chercher des formations en {{ keywords[0] }}</span>
              </HoverNote>
            </BusyButton>
          </template>
        </EmptyState>
        <!-- Aucun résultat (règles §4) : une ligne grise et « Effacer les filtres ». -->
        <p
          v-else-if="!sections.length"
          class="muted empty"
          data-test="trainings-no-result"
        >
          Aucune formation avec ces filtres.
          <button
            v-if="activeFilters"
            type="button"
            class="link"
            data-test="trainings-reset"
            @click="clearFilters"
          >
            Effacer les filtres
          </button>
        </p>
        <div
          v-else
          class="training-groups"
        >
          <section
            v-for="section in sections"
            :key="section.key"
            class="training-section"
            :aria-labelledby="`training-${section.key}`"
            :data-test="`training-section-${section.key}`"
          >
            <h2 :id="`training-${section.key}`">
              <span>{{ section.label }}</span><span>{{ phone ? section.items.length : plural(section.items.length, "formation", "formations") }}</span>
            </h2>
            <ul class="training-list">
              <li
                v-for="training in section.items"
                :key="training.id"
              >
                <TrainingRow
                  :training="training"
                  @open="openId = training.id"
                  @interest="toggleInterest(training)"
                  @review="(keep) => review(training, keep)"
                />
              </li>
            </ul>
          </section>
        </div>
        <p
          v-if="message"
          class="hint"
          role="status"
        >
          {{ message }}
        </p>
        <PushTransition>
          <DomainField
            v-if="domainFieldOpen && !hasDomain"
            id="domaine-champ"
            @saved="onDomainSaved"
          />
        </PushTransition>
        <!-- La recherche par domaine (B17) : sous la liste, « Chercher d'autres formations ». -->
        <BusyButton
          v-if="canSuggest && !domainEmpty"
          class="secondary action-2 training-suggest"
          :busy="suggesting"
          busy-label="Recherche en cours…"
          data-test="suggest"
          @click="suggest"
        >
          <HoverNote :text="suggesting ? '' : aiNote('Environ 0,02 à 0,05 $.')">
            Chercher d’autres formations
          </HoverNote>
        </BusyButton>
      </template>
    </div>
  </section>
  <!-- « Formation et chômage » (B16) : ce qu'il faut savoir avant de s'inscrire, et les pages officielles. -->
  <BottomSheet
    :open="fundingOpen"
    title="Formation et chômage"
    @close="fundingOpen = false"
  >
    <div
      class="training-funding-sheet"
      data-test="orp-sheet"
    >
      <p>L’ORP peut financer une formation. Il faut d’abord la demander à l’ORP et attendre son accord, avant de t’inscrire.</p>
      <a
        v-for="link in ORP_LINKS"
        :key="link.url"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
      >{{ link.label }}<span>nouvel onglet</span></a>
    </div>
    <template #actions>
      <button
        type="button"
        class="primary"
        data-test="orp-sheet-close"
        @click="fundingOpen = false"
      >
        Compris
      </button>
    </template>
  </BottomSheet>
  <BottomSheet
    :open="!!progressOf"
    title="Noter l’avancement"
    data-test="progress-sheet"
    @close="progressId = null"
  >
    <TrainingModules
      v-if="progressOf && progressOf.mark?.modules_total"
      :title="progressOf.title"
      :total="progressOf.mark.modules_total"
      :done="progressOf.mark.modules_done ?? 0"
      @save="(done) => mark(progressOf!, progressOf!.mark!.status, { modules_done: done })"
      @finish="(done) => { mark(progressOf!, 'done', { modules_done: done }); progressId = null; }"
    />
  </BottomSheet>
  <!-- Le suivi dans le panneau latéral, sur ordinateur comme sur téléphone (docs/44 §2). -->
  <SidePanel
    v-if="opened"
    open
    :title="opened.title"
    @close="openId = null"
  >
    <div class="training-card training-sheet">
      <TrainingCardBody
        :training="opened"
        variant="panel"
        @mark="(status, extra) => mark(opened!, status, extra)"
        @review="(keep) => { review(opened!, keep); if (!keep) openId = null; }"
        @linked="(linked) => replace({ ...opened!, mark: linked })"
      />
    </div>
  </SidePanel>
</template>

<style>
/* Bilan › Formations sur ordinateur (planche BilanOrdinateur, état Formations ; Kevin, 2026-11-14) : la carte de
   l'ORP, En cours, Gardées, puis « Chercher d'autres formations » qui ouvre le catalogue inchangé. Ici et non
   dans style.css : chargé avec la page, rien au premier écran (limites de poids du 13.11). */
@media (min-width: 821px) {
  .bilan-page-formations > .band { padding: 0; border-top: 0; }
  .bilan-page-formations > .band > .container { padding: 0; }
}
.trainings-overview { --tw-10: 10px; --tw-14: 14px; --tw-18: 18px; --tw-15: 0.9375rem; --tw-13: 0.8125rem; --tw-bar: 6px; --tw-lh: 21px; --tw-row: 56px; display: grid; gap: var(--space-8); }
.training-orp-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--tw-18) var(--space-6); background: var(--surface); border: 1px solid var(--water); border-radius: var(--radius-card); box-shadow: var(--shadow-band-card); }
.training-orp-card > span:first-child { display: grid; flex: 1; min-width: 0; }
.training-orp-card > span > span { font-size: var(--font-small); color: var(--text-secondary); }
.training-orp-how { display: inline-flex; flex: none; align-items: center; gap: var(--space-1); min-height: var(--target-min); font-size: var(--tw-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.training-block { display: grid; gap: var(--tw-10); }
.training-block .bilan-section-head h2 { font-size: var(--font-title); }
.training-block-list { margin: 0; padding: 0; overflow: hidden; list-style: none; background: var(--surface); border-radius: var(--radius-card); }
.training-block-list > li + li { border-top: 1px solid var(--surface-muted); }
.training-now { display: grid; gap: var(--space-3); padding: var(--space-4) var(--space-5); }
.training-now-head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-4); }
.training-now-head > .training-now-open, .training-kept-text { display: grid; grid-template-columns: minmax(0, 1fr); flex: 1; min-width: 0; }
.training-now-open { gap: 0; padding: 0; border: 0; background: none; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.training-now-open > span, .training-kept-text > span { font-size: var(--font-small); color: var(--text-secondary); }
.training-now-continue, .training-more { display: inline-flex; flex: none; align-items: center; justify-content: center; box-sizing: border-box; height: var(--target-min); padding: 0 var(--tw-18); border: var(--action-line) solid var(--primary-graphic); border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--tw-15); font-weight: var(--weight-semibold); white-space: nowrap; text-decoration: none; }
.training-now-continue:hover, .training-more:hover { background: var(--primary-soft); }
.training-more { justify-self: start; }
/* Le compteur de modules garde − et + (fonction de main) ; la barre et « Module 3 sur 12 » sur une ligne. */
.training-now .training-modules { grid-template-columns: minmax(0, 1fr) auto; align-items: center; column-gap: var(--space-3); }
.training-now .training-modules-bar { grid-row: 1; grid-column: 1; height: var(--tw-bar); background: var(--surface-muted); }
.training-now .training-modules-line { grid-row: 1; grid-column: 2; }
.training-now .training-modules-line strong { font-size: var(--tw-13); font-weight: var(--weight-regular); color: var(--text-secondary); }
.training-now .training-modules-line span { display: none; }
.training-now .training-modules-finish { grid-column: 1 / -1; }
.training-now-update { justify-self: start; min-height: var(--target-min); font-size: var(--tw-15); }
.training-kept-row { display: flex; align-items: center; gap: var(--tw-14); width: 100%; min-height: var(--tw-row); padding: var(--space-3) var(--space-5); border: 0; border-radius: 0; background: none; color: var(--text); font-size: var(--tw-15); font-weight: var(--weight-regular); line-height: var(--tw-lh); text-align: left; white-space: normal; }
.training-kept-row:hover { background: var(--surface-muted); }
.training-kept-text > span { margin-top: var(--space-1); }
.training-kept-status { display: inline-flex; flex: none; align-items: center; gap: var(--space-1); font-weight: var(--weight-bold); color: var(--text); }
.training-kept-status.accepted, .training-kept-status.granted, .training-kept-status.done { color: var(--success); }
.training-kept-status.refused { color: var(--text-secondary); }
/* En cours sans modules (planche BilanOrdinateurFormEtats, 16.11) : le texte libre et « Noter l'avancement » sur une ligne. */
.training-now { grid-template-columns: minmax(0, 1fr) auto; }
.training-now > * { grid-column: 1 / -1; }
.training-now > .training-current-progress { grid-column: 1; align-self: center; font-size: var(--tw-15); font-weight: var(--weight-regular); color: var(--text-tertiary); }
.training-now > .training-current-progress + .training-now-actions { grid-column: 2; }
/* Le catalogue sur ordinateur (planche BilanOrdinateurCatalogue, 16.11) : « ← Mes formations », les puces (la
   choisie en plein), une colonne de groupes, des lignes d'une ligne de détails et le signet rond de 44 px. */
.trainings-desk { --td-8: 8px; --td-12: 12px; --td-15: 0.9375rem; --td-72: 72px; gap: var(--space-8); }
.training-back { display: inline-flex; justify-self: start; align-items: center; gap: var(--td-8); min-height: var(--target-min); margin: calc(var(--td-12) * -1) 0 calc(var(--td-8) * -1); font-size: var(--td-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.training-chips-sep { display: none; }
.trainings-desk .training-chips { margin-top: calc(var(--td-8) * -1); }
.trainings-desk .training-chips-sep { display: block; flex: none; width: 1px; height: var(--space-6); margin: var(--td-8) var(--space-1); background: var(--button-outline); }
.trainings .training-chip { font-size: var(--td-15); font-weight: var(--weight-semibold); }
.trainings .training-chip[aria-pressed="true"] { border-color: var(--text); background: var(--text); color: var(--bg); }
.trainings .training-section h2 { align-items: baseline; font-size: var(--font-title); letter-spacing: 0; text-transform: none; color: var(--text); }
.trainings .training-section h2 span:last-child { font-size: var(--font-small); font-weight: var(--weight-regular); color: var(--text-secondary); }
.trainings-desk .training-row-open { gap: var(--space-4); min-height: var(--td-72); padding-left: var(--space-5); }
.trainings-desk .training-row-icon { border-radius: var(--td-12); background: var(--primary-soft); color: var(--primary-text); }
.trainings-desk .training-row-icon.cert { background: var(--peach-soft); color: var(--peach-text); }
.trainings-desk .training-row-text { display: flex; flex-wrap: wrap; align-items: center; gap: 0 var(--td-8); }
.trainings-desk .training-row-text > strong { flex-basis: 100%; font-size: var(--td-15); }
.trainings-desk .training-funding-note > span:nth-child(2) { gap: 0; }
.trainings-desk .training-funding-note > span:nth-child(2) > span { color: var(--peach-text); }
.trainings-desk .training-funding-icon { width: 2.5rem; height: 2.5rem; }
.trainings .training-keep { width: var(--target-min); height: var(--target-min); margin-right: var(--space-4); border: 1.5px solid var(--button-outline); border-radius: var(--radius-pill); color: var(--primary-text); }
.trainings .training-keep.on { border-color: var(--primary-soft); background: var(--primary-soft); }
.training-now-actions { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
/* Téléphone (planches BilanFormations et BilanCatalogue du 16.11, §37) : sections espacées de 22, intertitres de 17 ;
   En cours et Gardées en cartes séparées à filet de 1,5 px ; la barre puis « Module 3 sur 12 » ; « Noter
   l'avancement » à gauche, « Continuer le cours » à droite ; Gardées sur 2 lignes, statut en pastille ; catalogue sans
   icône, titre sur une ligne, « organisme · format » et le prix en pastille, signet rond de 44 px. */
@media (max-width: 820px) {
  .trainings { --td-8: 8px; --td-12: 12px; --td-15: 0.9375rem; --td-13: 0.8125rem; --td-17: 1.0625rem; --td-chip-r: 6px; }
  .trainings-overview { grid-template-columns: minmax(0, 1fr); gap: var(--space-6); }
  .training-orp-card { gap: var(--space-3); width: 100%; padding: var(--space-4); color: var(--text); font: inherit; font-weight: var(--weight-regular); text-align: left; }
  .training-orp-card strong { font-size: var(--tw-15); }
  .training-orp-card > span > span { font-size: var(--tw-13); }
  .training-block { gap: var(--space-2); }
  .training-block .bilan-section-head h2, .trainings .training-section h2 { font-size: var(--td-17); }
  .training-block-list { display: grid; gap: var(--space-2); overflow: visible; background: none; }
  .training-block-list > li, .trainings .training-list { overflow: hidden; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
  .training-block-list > li + li { border-top: 1.5px solid var(--card-line); }
  .training-now { gap: 0; padding: var(--space-4); }
  .training-now-head strong, .training-kept-text strong, .training-row-text > strong { overflow-wrap: anywhere; }
  .training-now-open > span { margin-top: var(--space-1); }
  .training-now .training-modules { grid-template-columns: 1fr; row-gap: var(--space-2); margin-top: var(--space-3); }
  .training-now .training-modules-line { grid-row: 2; grid-column: 1; }
  .training-now > .training-current-progress { margin-top: var(--space-3); font-size: var(--font-small); color: var(--text-lead); }
  .training-now-actions { margin-top: var(--space-3); }
  .training-kept-row { min-height: 68px; padding: var(--space-3) var(--space-4); }
  .training-kept-text > span { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-1); }
  .training-kept-text > span > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .training-kept-status, .training-row-tags > .training-tag { padding: var(--space-1) var(--space-2); border-radius: var(--td-chip-r); font-size: var(--font-caption); line-height: normal; }
  .training-kept-status { gap: var(--space-1); background: var(--success-soft); }
  .training-kept-status .icon { width: 12px; height: 12px; }
  .training-more { width: 100%; }
  .training-row-icon { display: none; }
  .training-row-open { min-height: 68px; padding: var(--space-3) 0 var(--space-3) var(--space-4); }
  .training-row-text { display: grid; grid-template-columns: minmax(0, max-content) auto; justify-content: start; align-items: center; gap: var(--space-1) var(--space-2); }
  .training-row-text > strong { grid-column: 1 / -1; font-size: var(--td-15); }
  .training-row-text > span:nth-child(2) { min-width: 0; overflow: hidden; font-size: var(--td-13); text-overflow: ellipsis; white-space: nowrap; }
  .trainings .training-keep { margin-right: var(--space-3); }
}
</style>
