<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter, type RouteLocationRaw } from "vue-router";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { useAuth } from "../composables/useAuth";
import { UNDO_MS } from "../composables/useUndo";
import { colorIndex, scoreWord } from "../format";
import { applicationLine, companyLine, followMessage } from "../searchText";
import AppIcon from "./AppIcon.vue";

// La recherche globale (série du 27.10, point 2 ; planche « 2. Recherche globale ») : dans tes offres,
// tes candidatures et tes entreprises (NN/g : une recherche visible sur ordinateur, dans ses propres
// données). Ordinateur : un champ dans l'en-tête, les résultats dans un panneau dessous. Téléphone (et
// écran étroit) : la loupe, puis la recherche en plein écran. Clavier : flèches, Entrée, Échap (W3C APG,
// combobox). En bas, « Suivre cette recherche » : un clic crée la recherche d'alerte, sans étape avant ;
// la confirmation dit ce qui reste à faire, et ne dit jamais « suivie » tant qu'une alerte reste à créer.
type Results = components["schemas"]["GlobalSearchOut"];
type Follow = components["schemas"]["FollowOut"];

const router = useRouter();
const { me } = useAuth();

// Sous 1 100 px, la place manque dans l'en-tête : la loupe seule, comme sur téléphone.
const COMPACT = "(max-width: 1099px)";
const compact = ref(globalThis.matchMedia?.(COMPACT).matches ?? false);
let media: MediaQueryList | undefined;
const onMedia = (): void => {
  compact.value = media?.matches ?? false;
};

const q = ref("");
const open = ref(false);
const results = ref<Results | null>(null);
const active = ref(-1);
const followed = ref<Follow | null>(null);
const status = ref("");
const busy = ref(false);
const undoLeft = ref(0);
let undoTimer: ReturnType<typeof setInterval> | undefined;
const input = ref<HTMLInputElement | null>(null);
const root = ref<HTMLElement | null>(null);

const terms = computed(() => q.value.trim());
const now = new Date();

// Une option par résultat, puis « Suivre cette recherche » : la liste que parcourent les flèches.
type Option = { id: string; kind: "offer" | "application" | "company" | "follow"; to?: RouteLocationRaw };
const options = computed<Option[]>(() => {
  const r = results.value;
  const list: Option[] = [];
  if (r) {
    for (const o of r.offers.items) list.push({ id: `gs-offer-${o.id}`, kind: "offer", to: { path: "/candidatures/offres", query: { offre: String(o.id), statut: "all" } } });
    for (const a of r.applications.items) list.push({ id: `gs-app-${a.id}`, kind: "application", to: { path: "/candidatures/suivi", query: { candidature: String(a.id), ...(a.orp_month ? { mois: a.orp_month } : {}) } } });
    for (const c of r.companies.items) list.push({ id: `gs-company-${normalize(c.name)}`, kind: "company", to: { path: "/candidatures/offres", query: { q: c.name, statut: "all" } } });
  }
  if (terms.value.length >= 2 && !followed.value) list.push({ id: "gs-follow", kind: "follow" });
  return list;
});
const activeId = computed(() => options.value[active.value]?.id);
const empty = computed(() => !!results.value && !results.value.offers.total && !results.value.applications.total && !results.value.companies.total);

function normalize(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

let timer: ReturnType<typeof setTimeout> | undefined;
let seq = 0;
watch(q, () => {
  followed.value = null;
  status.value = "";
  active.value = -1;
  clearTimeout(timer);
  if (terms.value.length < 2) {
    results.value = null;
    return;
  }
  timer = setTimeout(() => void load(), 250);
});

async function load(): Promise<void> {
  const current = ++seq;
  const { data } = await api.GET("/api/search", { params: { query: { q: terms.value } } });
  if (current === seq) results.value = data ?? null;
}

function go(to: RouteLocationRaw): void {
  close();
  void router.push(to);
}

function choose(option: Option | undefined): void {
  if (!option) return;
  if (option.kind === "follow") void follow();
  else if (option.to) go(option.to);
}

function onKeydown(event: KeyboardEvent): void {
  const count = options.value.length;
  if (event.key === "ArrowDown" && count) {
    event.preventDefault();
    open.value = true;
    active.value = (active.value + 1) % count;
  } else if (event.key === "ArrowUp" && count) {
    event.preventDefault();
    active.value = active.value <= 0 ? count - 1 : active.value - 1;
  } else if (event.key === "Enter" && active.value >= 0) {
    event.preventDefault();
    choose(options.value[active.value]);
  } else if (event.key === "Escape") {
    event.preventDefault();
    close();
  }
}

// La recherche suivie : un clic, puis la confirmation à la place des résultats (WCAG 4.1.3).
const message = computed(() => (followed.value ? followMessage(followed.value) : null));
async function follow(): Promise<void> {
  if (busy.value || terms.value.length < 2) return;
  busy.value = true;
  status.value = "";
  try {
    const { data } = await api.POST("/api/alert-searches/follow", { body: { terms: terms.value } });
    if (!data) {
      status.value = me.value?.demo ? "Démo : rien n'est enregistré." : "La recherche n'a pas pu être ajoutée. Réessaie.";
      return;
    }
    followed.value = data;
    active.value = -1;
    // « Annuler » pendant 6 s (§4) : il retire ce qui vient d'être créé.
    undoLeft.value = Math.round(UNDO_MS / 1000);
    clearInterval(undoTimer);
    undoTimer = setInterval(() => {
      undoLeft.value -= 1;
      if (undoLeft.value <= 0) clearInterval(undoTimer);
    }, 1000);
  } finally {
    busy.value = false;
  }
}

async function cancelFollow(): Promise<void> {
  const done = followed.value;
  if (!done) return;
  clearInterval(undoTimer);
  undoLeft.value = 0;
  for (const id of done.created) await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: id } } });
  followed.value = null;
  status.value = "Recherche retirée.";
}

function show(): void {
  open.value = true;
  if (compact.value) void nextTick(() => input.value?.focus());
}
function close(): void {
  open.value = false;
  active.value = -1;
}

// Un clic hors de la recherche la referme (ordinateur).
function onPointerDown(event: PointerEvent): void {
  if (!open.value || compact.value) return;
  if (event.target instanceof Node && root.value?.contains(event.target)) return;
  close();
}
watch([open, compact], ([isOpen, isCompact]) => {
  document.documentElement.classList.toggle("search-open", isOpen && isCompact);
});

onMounted(() => {
  media = globalThis.matchMedia?.(COMPACT);
  media?.addEventListener("change", onMedia);
  document.addEventListener("pointerdown", onPointerDown);
});
onUnmounted(() => {
  media?.removeEventListener("change", onMedia);
  document.removeEventListener("pointerdown", onPointerDown);
  document.documentElement.classList.remove("search-open");
  clearInterval(undoTimer);
});

const panelVisible = computed(() => open.value && (compact.value || terms.value.length >= 2 || !!status.value));
</script>

<template>
  <div
    ref="root"
    :class="['global-search', { compact }]"
    data-test="global-search"
  >
    <button
      v-if="compact"
      type="button"
      class="header-round"
      aria-label="Rechercher"
      data-label="Rechercher"
      data-test="search-open"
      @click="show"
    >
      <AppIcon name="search" />
    </button>
    <Teleport
      to="body"
      :disabled="!compact"
    >
      <div
        v-if="!compact || open"
        :class="['global-search-box', { sheet: compact }]"
      >
        <div class="global-search-field">
          <label
            for="global-search-input"
            class="visually-hidden"
          >Rechercher</label>
          <span class="global-search-input-wrap">
            <AppIcon name="search" />
            <input
              id="global-search-input"
              ref="input"
              v-model="q"
              type="search"
              role="combobox"
              autocomplete="off"
              placeholder="Offres, candidatures, entreprises"
              aria-autocomplete="list"
              aria-controls="global-search-results"
              :aria-expanded="panelVisible"
              :aria-activedescendant="activeId"
              data-test="search-input"
              @focus="open = true"
              @keydown="onKeydown"
            >
          </span>
          <button
            v-if="compact"
            type="button"
            class="link"
            data-test="search-close"
            @click="close"
          >
            Fermer
          </button>
        </div>
        <div
          v-if="panelVisible"
          class="global-search-panel"
          data-test="search-panel"
        >
          <!-- La confirmation à la place des résultats (WCAG 4.1.3). -->
          <div
            v-if="followed && message"
            class="gs-followed"
            role="status"
            data-test="search-followed"
          >
            <span
              class="gs-bubble"
              aria-hidden="true"
            ><AppIcon name="done" /></span>
            <div class="gs-followed-text">
              <p class="gs-followed-title">
                {{ message.title }}
              </p>
              <p
                v-if="message.todo"
                class="gs-todo"
                data-test="search-todo"
              >
                {{ message.todo }}
              </p>
              <div class="gs-actions">
                <button
                  v-if="message.todo"
                  type="button"
                  class="primary"
                  data-test="search-create-alerts"
                  @click="go({ path: '/candidatures/alertes', query: { recherche: followed.terms } })"
                >
                  Créer les alertes
                </button>
                <button
                  type="button"
                  class="link"
                  data-test="search-edit"
                  @click="go({ path: '/candidatures/alertes', query: { gerer: '1' } })"
                >
                  Modifier
                </button>
                <button
                  v-if="undoLeft > 0 && followed.created.length"
                  type="button"
                  class="link"
                  data-test="search-undo"
                  @click="cancelFollow"
                >
                  Annuler ({{ undoLeft }} s)
                </button>
              </div>
            </div>
          </div>
          <template v-else>
            <p
              v-if="status"
              class="gs-status"
              role="status"
            >
              {{ status }}
            </p>
            <div
              v-if="results"
              id="global-search-results"
              role="listbox"
              aria-label="Résultats de la recherche"
              data-test="search-results"
            >
              <p
                v-if="empty"
                class="gs-empty"
                data-test="search-empty"
              >
                Aucun résultat pour « {{ terms }} » dans tes offres, candidatures et entreprises.
              </p>
              <div
                v-if="results.offers.items.length"
                class="gs-group"
                role="group"
                aria-labelledby="gs-offers"
              >
                <div class="gs-group-head">
                  <span
                    id="gs-offers"
                    class="gs-group-title"
                  >Offres</span>
                  <RouterLink
                    v-if="results.offers.total > 3"
                    :to="{ path: '/candidatures/offres', query: { q: terms, statut: 'all' } }"
                    class="link"
                    data-test="search-all-offers"
                    @click="close"
                  >
                    Tout voir ({{ results.offers.total }})
                  </RouterLink>
                </div>
                <div
                  v-for="o in results.offers.items"
                  :id="`gs-offer-${o.id}`"
                  :key="o.id"
                  role="option"
                  :aria-selected="activeId === `gs-offer-${o.id}`"
                  :class="['gs-row', { active: activeId === `gs-offer-${o.id}` }]"
                  data-test="search-offer"
                  @click="choose(options.find((x) => x.id === `gs-offer-${o.id}`))"
                >
                  <span
                    :class="['logo', `c${colorIndex(o.company ?? o.title)}`]"
                    aria-hidden="true"
                  >{{ (o.company ?? o.title).charAt(0).toUpperCase() }}</span>
                  <span class="gs-text">
                    <strong>{{ o.title }}</strong>
                    <span>{{ [o.company, o.location].filter(Boolean).join(" · ") }}</span>
                  </span>
                  <span
                    v-if="o.score !== null && o.score !== undefined"
                    :class="['gs-verdict', scoreWord(o.score).tone]"
                  >{{ scoreWord(o.score).word }}</span>
                </div>
              </div>
              <div
                v-if="results.applications.items.length"
                class="gs-group"
                role="group"
                aria-labelledby="gs-applications"
              >
                <div class="gs-group-head">
                  <span
                    id="gs-applications"
                    class="gs-group-title"
                  >Candidatures</span>
                  <span
                    v-if="results.applications.total > 3"
                    class="gs-more"
                  >{{ results.applications.total }} en tout</span>
                </div>
                <div
                  v-for="a in results.applications.items"
                  :id="`gs-app-${a.id}`"
                  :key="a.id"
                  role="option"
                  :aria-selected="activeId === `gs-app-${a.id}`"
                  :class="['gs-row', { active: activeId === `gs-app-${a.id}` }]"
                  data-test="search-application"
                  @click="choose(options.find((x) => x.id === `gs-app-${a.id}`))"
                >
                  <span
                    :class="['logo', `c${colorIndex(a.company)}`]"
                    aria-hidden="true"
                  >{{ a.company.charAt(0).toUpperCase() }}</span>
                  <span class="gs-text">
                    <strong>{{ a.job_title }}</strong>
                    <span>{{ applicationLine(a, now) }}</span>
                  </span>
                </div>
              </div>
              <div
                v-if="results.companies.items.length"
                class="gs-group"
                role="group"
                aria-labelledby="gs-companies"
              >
                <div class="gs-group-head">
                  <span
                    id="gs-companies"
                    class="gs-group-title"
                  >Entreprises</span>
                  <span
                    v-if="results.companies.total > 3"
                    class="gs-more"
                  >{{ results.companies.total }} en tout</span>
                </div>
                <div
                  v-for="c in results.companies.items"
                  :id="`gs-company-${normalize(c.name)}`"
                  :key="c.name"
                  role="option"
                  :aria-selected="activeId === `gs-company-${normalize(c.name)}`"
                  :class="['gs-row', { active: activeId === `gs-company-${normalize(c.name)}` }]"
                  data-test="search-company"
                  @click="choose(options.find((x) => x.id === `gs-company-${normalize(c.name)}`))"
                >
                  <span
                    :class="['logo', `c${colorIndex(c.name)}`]"
                    aria-hidden="true"
                  >{{ c.name.charAt(0).toUpperCase() }}</span>
                  <span class="gs-text">
                    <strong>{{ c.name }}</strong>
                    <span>{{ companyLine(c) }}</span>
                  </span>
                </div>
              </div>
              <!-- En bas, et aussi sans résultat : suivre ces mots dans les alertes. -->
              <div
                v-if="terms.length >= 2"
                id="gs-follow"
                role="option"
                :aria-selected="activeId === 'gs-follow'"
                :class="['gs-row', 'gs-follow', { active: activeId === 'gs-follow' }]"
                data-test="search-follow"
                @click="follow"
              >
                <span
                  class="gs-bubble"
                  aria-hidden="true"
                ><AppIcon name="bell" /></span>
                <span class="gs-text">
                  <strong class="gs-follow-title">Suivre cette recherche</strong>
                  <span>Ajoute « {{ terms }} » à tes alertes, avec les lieux de ton profil et tes sites suivis.</span>
                </span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>
