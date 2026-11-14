<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type Training } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import BusyButton from "../components/BusyButton.vue";
import CountBadge from "../components/CountBadge.vue";
import DomainField from "../components/DomainField.vue";
import FaceState from "../components/FaceState.vue";
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
import { FUNDING, ORP_LINKS, SHORT_FORMATS } from "../trainingLabels";

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
// formations » (`?onglet=catalogue`). Téléphone inchangé : le catalogue d'abord, Suivies en `?onglet=miennes`.
const tab = computed<"catalog" | "mine">(() => {
  const onglet = route.query.onglet;
  if (onglet === "miennes") return "mine";
  return phone.value || onglet === "catalogue" ? "catalog" : "mine";
});
const overview = computed(() => !phone.value && tab.value === "mine");
const catalogTo = computed(() => (phone.value ? { query: {} } : { query: { onglet: "catalogue" } }));
const mineTo = computed(() => (phone.value ? { query: { onglet: "miennes" } } : { query: {} }));
const items = ref<Training[]>([]);
const keywords = ref<string[]>([]);
const canSuggest = ref(false);
const loaded = ref(false);
usePageReady("trainings", () => loaded.value);
const domainOnly = ref(true);
const suggesting = ref(false);
const message = ref("");

const hasDomain = computed(() => keywords.value.length > 0);

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
    <div class="container trainings">
      <!-- Catalogue · Suivies, soulignés (second niveau, S4 ; B15), le nombre de suivies en pastille. -->
      <nav
        v-if="!overview"
        class="trainings-tabs"
        aria-label="Formations affichées"
      >
        <RouterLink
          :to="catalogTo"
          :class="{ active: tab === 'catalog' }"
          :aria-current="tab === 'catalog' ? 'true' : undefined"
          data-test="tab-catalog"
        >
          Catalogue
        </RouterLink>
        <RouterLink
          :to="mineTo"
          :class="{ active: tab === 'mine' }"
          :aria-current="tab === 'mine' ? 'true' : undefined"
          data-test="tab-mine"
        >
          Suivies<CountBadge
            v-if="mineCount"
            class="tab-count"
            :count="mineCount"
          />
        </RouterLink>
      </nav>

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
        <div
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
        <FaceState
          v-if="!mineCount"
          title="Aucune formation suivie"
          illustration="formations-vide"
          data-test="trainings-none"
        >
          <p>Garde une formation du catalogue avec son signet.</p>
        </FaceState>
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
                <span>
                  <strong>{{ training.title }}</strong>
                  <span>{{ training.provider }}</span>
                </span>
                <a
                  :href="training.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="training-now-continue"
                  data-test="training-continue"
                >Continuer le cours<span class="visually-hidden"> (nouvel onglet)</span></a>
              </div>
              <TrainingModules
                v-if="training.mark!.modules_total"
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
                {{ training.mark!.progress || "En cours" }}
              </p>
              <button
                type="button"
                class="link training-now-update"
                data-test="training-update"
                @click="openId = training.id"
              >
                Noter l’avancement
              </button>
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
                  <span>{{ keptMeta(training) }}</span>
                </span>
                <span
                  v-if="keptStatus(training)"
                  :class="['training-kept-status', keptStatus(training)!.tone]"
                  data-test="training-kept-status"
                >{{ keptStatus(training)!.label }}</span>
                <span
                  class="arrow-circle small"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span>
              </button>
            </li>
          </ul>
        </section>
        <RouterLink
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
          <span><strong>Financement possible par l’ORP</strong><span>Seulement avec l’accord préalable de l’ORP</span></span>
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
        <!-- Aucun résultat (règles §4) : une ligne grise et « Effacer les filtres ». -->
        <p
          v-if="!sections.length"
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
              <span>{{ section.label }}</span><span>{{ section.items.length }}</span>
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
          v-if="canSuggest"
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
      <!-- Aucune formation suivie (planche « Illustrations »). -->
      <FaceState
        v-else-if="!mineCount"
        title="Aucune formation suivie"
        illustration="formations-vide"
        data-test="trainings-none"
      >
        <p>Garde une formation du catalogue avec son signet.</p>
      </FaceState>
      <div
        v-else
        class="training-mine"
      >
        <!-- En cours (B19) : la carte avec l'avancement noté, en attendant le compteur de modules. -->
        <section
          v-for="training in inProgress"
          :key="training.id"
          class="training-current"
          :aria-labelledby="`training-current-${training.id}`"
          data-test="training-current"
        >
          <div class="training-current-head">
            <span
              :class="['training-row-icon', { cert: training.kind === 'certification' }]"
              aria-hidden="true"
            ><AppIcon :name="training.kind === 'certification' ? 'star' : 'book'" /></span>
            <span>
              <strong :id="`training-current-${training.id}`">{{ training.title }}</strong>
              <span>{{ training.provider }}</span>
            </span>
          </div>
          <TrainingModules
            v-if="training.mark!.modules_total"
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
            {{ training.mark!.progress || "En cours" }}
          </p>
          <div class="training-current-actions">
            <a
              :href="training.url"
              target="_blank"
              rel="noopener noreferrer"
              class="action-2"
              data-test="training-continue"
            >Continuer le cours<span class="visually-hidden"> (nouvel onglet)</span><AppIcon name="external" /></a>
            <button
              type="button"
              class="link"
              data-test="training-update"
              @click="openId = training.id"
            >
              Noter l’avancement
            </button>
          </div>
        </section>
        <ul
          v-if="others.length"
          class="training-kept"
        >
          <li
            v-for="training in others"
            :key="training.id"
            data-test="training-kept"
          >
            <span>
              <strong>{{ training.title }}</strong>
              <span>{{ training.mark!.status === "done" ? "Terminée" : "Gardée · pas encore commencée" }}</span>
            </span>
            <button
              type="button"
              class="training-see"
              :aria-label="`Voir : ${training.title}`"
              @click="openId = training.id"
            >
              <span
                class="arrow-circle small"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </button>
          </li>
        </ul>
        <p class="training-help">
          Le signet du catalogue range une formation ici. Elle passe « en cours » au premier module.
        </p>
      </div>
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
.training-orp-card > span { display: grid; flex: 1; min-width: 0; }
.training-orp-card > span > span { font-size: var(--font-small); color: var(--text-secondary); }
.training-orp-how { display: inline-flex; flex: none; align-items: center; gap: var(--space-1); min-height: var(--target-min); font-size: var(--tw-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.training-block { display: grid; gap: var(--tw-10); }
.training-block .bilan-section-head h2 { font-size: var(--font-title); }
.training-block-list { margin: 0; padding: 0; overflow: hidden; list-style: none; background: var(--surface); border-radius: var(--radius-card); }
.training-block-list > li + li { border-top: 1px solid var(--surface-muted); }
.training-now { display: grid; gap: var(--space-3); padding: var(--space-4) var(--space-5); }
.training-now-head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-4); }
.training-now-head > span, .training-kept-text { display: grid; flex: 1; min-width: 0; }
.training-now-head > span > span, .training-kept-text > span { font-size: var(--font-small); color: var(--text-secondary); }
.training-now-continue, .training-more { display: inline-flex; flex: none; align-items: center; justify-content: center; box-sizing: border-box; height: var(--target-min); padding: 0 var(--tw-18); border: var(--action-line) solid var(--primary-graphic); border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--tw-15); font-weight: var(--weight-semibold); white-space: nowrap; text-decoration: none; }
.training-now-continue:hover, .training-more:hover { background: var(--primary-soft); }
.training-more { justify-self: start; }
/* Le compteur de modules garde − et + (fonction de main) ; la barre et « Module 3 sur 12 » sur une ligne. */
.training-now .training-modules { grid-template-columns: minmax(0, 1fr) auto; align-items: center; column-gap: var(--space-3); }
.training-now .training-modules-bar { grid-row: 1; grid-column: 1; height: var(--tw-bar); background: var(--surface-muted); }
.training-now .training-modules-line { grid-row: 1; grid-column: 2; }
.training-now .training-modules-line strong { font-size: var(--tw-13); font-weight: var(--weight-regular); color: var(--text-secondary); }
.training-now .training-modules-line span { display: none; }
.training-now .training-modules-step, .training-now .training-modules-finish { grid-column: 1 / -1; }
.training-now-update { justify-self: start; min-height: var(--target-min); font-size: var(--tw-15); }
.training-kept-row { display: flex; align-items: center; gap: var(--tw-14); width: 100%; min-height: var(--tw-row); padding: var(--space-3) var(--space-5); border: 0; border-radius: 0; background: none; color: var(--text); font-size: var(--tw-15); font-weight: var(--weight-regular); line-height: var(--tw-lh); text-align: left; white-space: normal; }
.training-kept-row:hover { background: var(--surface-muted); }
.training-kept-text > span { margin-top: var(--space-1); }
.training-kept-status { flex: none; font-weight: var(--weight-bold); color: var(--text); }
.training-kept-status.accepted, .training-kept-status.granted { color: var(--success); }
.training-kept-status.done, .training-kept-status.refused { color: var(--text-secondary); }
</style>
