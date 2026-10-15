<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type NewsItem, type NewsPage, type NewsPreferences } from "../api/client";
import DomainField from "../components/DomainField.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NewsStory from "../components/NewsStory.vue";
import PushTransition from "../components/PushTransition.vue";
import PageHero from "../components/PageHero.vue";
import IllustratedSide from "../components/IllustratedSide.vue";
import { useAuth } from "../composables/useAuth";
import { useNewsCount } from "../composables/useNewsCount";
import { usePhone } from "../composables/usePhone";
import { since } from "../format";
import { countryLabel, languageLabel } from "../newsLabels";

// Actualités (docs/15 §2, docs/16) : marché de l'emploi, économie et vidéos, filtrés selon ton
// domaine. « Marché de l'emploi » ne garde que l'emploi et ton domaine (docs/43 n° 16).
const POLL_MS = 4_000;
const POLL_LIMIT = 30; // deux minutes au plus

const route = useRoute();
type Tab = "jobs" | "economy" | "videos";
const tab = computed<Tab>(() => {
  if (route.query.rubrique === "videos") return "videos";
  return route.query.rubrique === "economie" ? "economy" : "jobs";
});
const items = ref<NewsItem[]>([]);
const page = ref<NewsPage | null>(null);
const preferences = ref<NewsPreferences | null>(null);
const counts = ref({ jobs: 0, economy: 0, videos: 0 });
const loaded = ref(false);
const { reset } = useNewsCount();
const { loggedIn } = useAuth();
let poll: ReturnType<typeof setTimeout> | undefined;
let polls = 0;

const { phone } = usePhone();
// Téléphone (docs/43 n° 17) : 10 contenus d'abord, puis « Voir plus », au lieu de 60 d'un coup.
const PHONE_STEP = 10;
const shown = ref(PHONE_STEP);
const visible = computed(() => (phone.value ? items.value.slice(0, shown.value) : items.value));
const hidden = computed(() => items.value.length - visible.value.length);

// À la manière de RTS (docs/35) : une actualité en tête (la plus récente qui a une image),
// deux en second rang sur ordinateur, puis des lignes groupées par période. Même chose pour
// les vidéos. Sur téléphone, seule l'actualité en tête est en grand.
const ordered = computed(() => {
  const lead = visible.value.find((item) => item.has_image) ?? visible.value[0];
  return lead ? [lead, ...visible.value.filter((item) => item !== lead)] : [];
});
const top = computed(() => ordered.value.slice(0, phone.value ? 1 : 3));
const PERIODS = [
  { key: "today", label: "Aujourd'hui" },
  { key: "week", label: "Cette semaine" },
  { key: "older", label: "Plus ancien" },
] as const;

function period(published: string, now = new Date()): (typeof PERIODS)[number]["key"] {
  const day = new Date(published);
  if (day.toDateString() === now.toDateString()) return "today";
  return now.getTime() - day.getTime() < 7 * 24 * 3600 * 1000 ? "week" : "older";
}

const groups = computed(() => {
  const rest = ordered.value.slice(top.value.length);
  return PERIODS.map((p) => ({ ...p, items: rest.filter((item) => period(item.published_at) === p.key) })).filter(
    (g) => g.items.length,
  );
});


// Pays et langue derrière « Filtrer » (docs/32 §5.2), avec le nombre de filtres actifs.
const filtersOpen = ref(false);
const filtersRoot = ref<HTMLElement | null>(null);
// Téléphone (retour du 2026-10-15) : comme les alertes, une carte sur toute la largeur sous
// la ligne des filtres, qui pousse la liste en douceur. Ordinateur : le menu déroulant.
const filtersPopover = ref<HTMLElement | null>(null);
const activeFilters = computed(() => (preferences.value?.countries.length ?? 0) + (preferences.value?.languages.length ?? 0));
const canFilter = computed(() => (page.value?.countries.length ?? 0) > 1 || (page.value?.languages.length ?? 0) > 1);

function onDocument(event: Event): void {
  const target = event.target as Node;
  if (!filtersRoot.value?.contains(target) && !filtersPopover.value?.contains(target)) closeFilters();
}

function toggleFilters(): void {
  filtersOpen.value = !filtersOpen.value;
  if (filtersOpen.value) document.addEventListener("pointerdown", onDocument);
  else document.removeEventListener("pointerdown", onDocument);
}

function closeFilters(): void {
  filtersOpen.value = false;
  document.removeEventListener("pointerdown", onDocument);
}
const hasDomain = computed(() => (preferences.value?.domain_keywords.length ?? 0) > 0);
// Sans domaine, « Mon domaine » ouvre le champ sur place (docs/43 n° 4).
const domainFieldOpen = ref(false);

function chooseDomain(): void {
  if (hasDomain.value) void savePreferences({ domain_only: true });
  else domainFieldOpen.value = !domainFieldOpen.value;
}

async function onDomainSaved(keywords: string[]): Promise<void> {
  domainFieldOpen.value = false;
  if (preferences.value) preferences.value = { ...preferences.value, domain_keywords: keywords, domain_only: true };
  await load();
}

async function load(): Promise<void> {
  const prefs = preferences.value;
  const { data } = await api.GET("/api/news", {
    params: {
      query: {
        kind: tab.value === "videos" ? "videos" : "articles",
        topic: tab.value === "videos" ? undefined : tab.value,
        limit: 60,
        domain_only: Boolean(prefs?.domain_only && hasDomain.value),
        country: prefs?.countries.length ? prefs.countries : undefined,
        language: prefs?.languages.length ? prefs.languages : undefined,
      },
    },
  });
  if (!data) return;
  page.value = data;
  items.value = data.items;
  if (!loaded.value) {
    counts.value = { jobs: data.new_jobs, economy: data.new_economy, videos: data.new_videos };
    // La visite remet les compteurs à zéro (pour la prochaine fois).
    // Sans connexion, rien n'est enregistré (docs/18 §1).
    if (loggedIn.value) await api.POST("/api/news/seen");
    reset();
  }
  loaded.value = true;
  schedulePoll();
}

// Pendant un relevé, la page se met à jour d'elle-même.
function schedulePoll(): void {
  clearTimeout(poll);
  if (!page.value?.refreshing || polls >= POLL_LIMIT) return;
  polls += 1;
  poll = setTimeout(() => void load(), POLL_MS);
}

async function refresh(): Promise<void> {
  const { data } = await api.POST("/api/news/refresh");
  if (data?.queued && page.value) {
    page.value = { ...page.value, refreshing: true };
    polls = 0;
    schedulePoll();
  }
}

async function savePreferences(change: Partial<NewsPreferences>): Promise<void> {
  if (!preferences.value) return;
  preferences.value = { ...preferences.value, ...change };
  await load();
  if (loggedIn.value) await api.PUT("/api/news/preferences", { body: preferences.value });
}

function toggle(list: "countries" | "languages", value: string): void {
  const current = preferences.value?.[list] ?? [];
  void savePreferences({ [list]: current.includes(value) ? current.filter((v) => v !== value) : [...current, value] });
}

const selected = (list: "countries" | "languages", value: string): boolean =>
  preferences.value?.[list].includes(value) ?? false;

watch(tab, () => {
  shown.value = PHONE_STEP;
  void load();
});
onMounted(async () => {
  const { data } = await api.GET("/api/news/preferences");
  preferences.value = data ?? null;
  await load();
});
onUnmounted(() => {
  clearTimeout(poll);
  closeFilters();
});
</script>

<template>
  <PageHero
    title="Le marché de l'emploi, et de quoi progresser"
    short="Actualités"
    subtitle="L'emploi et ton domaine : articles et vidéos récents."
  >
    <nav
      class="prep-tabs"
      aria-label="Actualités"
    >
      <RouterLink
        :to="{ query: {} }"
        :class="{ active: tab === 'jobs' }"
        data-test="tab-articles"
      >
        <span class="label-long">Marché de l'emploi</span>
        <span class="label-short">Emploi</span>
        <span
          v-if="counts.jobs"
          class="tab-count"
        >{{ counts.jobs }}</span>
      </RouterLink>
      <RouterLink
        :to="{ query: { rubrique: 'economie' } }"
        :class="{ active: tab === 'economy' }"
        data-test="tab-economy"
      >
        Économie
        <span
          v-if="counts.economy"
          class="tab-count"
        >{{ counts.economy }}</span>
      </RouterLink>
      <RouterLink
        :to="{ query: { rubrique: 'videos' } }"
        :class="{ active: tab === 'videos' }"
        data-test="tab-videos"
      >
        Vidéos
        <span
          v-if="counts.videos"
          class="tab-count"
        >{{ counts.videos }}</span>
      </RouterLink>
    </nav>
  </PageHero>
  <section class="band">
    <div class="container">
      <div
        v-if="preferences && page"
        class="news-filters"
        data-test="news-filters"
      >
        <div
          class="segmented"
          role="radiogroup"
          aria-label="Contenus affichés"
        >
          <button
            type="button"
            role="radio"
            :aria-checked="preferences.domain_only && hasDomain"
            :aria-expanded="hasDomain ? undefined : domainFieldOpen"
            data-test="filter-domain"
            @click="chooseDomain"
          >
            Mon domaine
          </button>
          <button
            type="button"
            role="radio"
            :aria-checked="!preferences.domain_only || !hasDomain"
            data-test="filter-all"
            @click="savePreferences({ domain_only: false })"
          >
            Tout
          </button>
        </div>
        <div
          v-if="canFilter"
          ref="filtersRoot"
          class="news-filter-menu"
          @keydown.esc="closeFilters"
        >
          <button
            type="button"
            class="secondary small"
            :aria-expanded="filtersOpen"
            aria-controls="news-filter-popover"
            data-test="news-filter-toggle"
            @click="toggleFilters"
          >
            Filtrer{{ activeFilters ? ` · ${activeFilters}` : "" }}
          </button>
          <Teleport
            to="#news-filter-drop"
            defer
            :disabled="!phone"
          >
            <PushTransition :enabled="phone">
              <div
                v-show="filtersOpen"
                id="news-filter-popover"
                class="news-filter-popover"
                data-test="news-filter-popover"
              >
                <div
                  v-if="page.countries.length > 1"
                  class="chip-group"
                  role="group"
                  aria-label="Pays"
                >
                  <span class="chip-label">Pays</span>
                  <button
                    v-for="code in page.countries"
                    :key="code"
                    type="button"
                    :class="['chip', { on: selected('countries', code) }]"
                    :aria-pressed="selected('countries', code)"
                    data-test="filter-country"
                    @click="toggle('countries', code)"
                  >
                    {{ countryLabel(code) }}
                  </button>
                </div>
                <div
                  v-if="page.languages.length > 1"
                  class="chip-group"
                  role="group"
                  aria-label="Langue"
                >
                  <span class="chip-label">Langue</span>
                  <button
                    v-for="code in page.languages"
                    :key="code"
                    type="button"
                    :class="['chip', { on: selected('languages', code) }]"
                    :aria-pressed="selected('languages', code)"
                    data-test="filter-language"
                    @click="toggle('languages', code)"
                  >
                    {{ languageLabel(code) }}
                  </button>
                </div>
              </div>
            </PushTransition>
          </Teleport>
        </div>
        <div
          id="news-filter-drop"
          class="filter-drop-zone"
        />
      </div>
      <PushTransition>
        <DomainField
          v-if="domainFieldOpen && !hasDomain"
          @saved="onDomainSaved"
        />
      </PushTransition>

      <LoadingBlocks
        v-if="!loaded"
        :heights="phone ? ['14rem', '5rem', '5rem'] : ['22rem', '6rem', '6rem']"
      />

      <IllustratedSide
        v-else-if="!items.length"
        class="empty-state empty"
        name="newsfeed"
        phone="small"
      >
        <p>
          <template v-if="page?.refreshing">
            Premier relevé en cours : les contenus arrivent dans quelques secondes.
          </template>
          <template v-else-if="preferences?.domain_only || preferences?.countries.length || preferences?.languages.length">
            Rien avec ces filtres pour l'instant.
          </template>
          <template v-else>
            Rien pour l'instant.
            <RouterLink to="/reglages?rubrique=actualites">
              Gérer les sources
            </RouterLink>
          </template>
        </p>
      </IllustratedSide>
      <div
        v-else
        :class="['news-modules', tab === 'videos' ? 'videos' : 'articles']"
      >
        <div :class="['news-top', `count-${top.length}`]">
          <NewsStory
            v-if="top[0]"
            :item="top[0]"
            variant="lead"
          />
          <div
            v-if="top.length > 1"
            class="news-second"
          >
            <NewsStory
              v-for="item in top.slice(1)"
              :key="item.id"
              :item="item"
              variant="second"
            />
          </div>
        </div>
        <section
          v-for="group in groups"
          :key="group.key"
          class="news-group"
        >
          <h2 class="news-group-title">
            {{ group.label }}
          </h2>
          <ul class="news-row-list">
            <li
              v-for="item in group.items"
              :key="item.id"
            >
              <NewsStory
                :item="item"
                variant="row"
              />
            </li>
          </ul>
        </section>
        <button
          v-if="hidden > 0"
          type="button"
          class="secondary news-more"
          data-test="news-more"
          @click="shown += PHONE_STEP"
        >
          Voir plus
        </button>
      </div>
      <p
        v-if="page"
        class="news-status"
      >
        <span
          v-if="page.refreshing"
          data-test="news-refreshing"
        >Relevé en cours…</span>
        <template v-else>
          <span v-if="page.fetched_at">Relevé {{ since(page.fetched_at) }}</span>
          <button
            type="button"
            class="link"
            data-test="news-refresh"
            @click="refresh"
          >
            Relever
          </button>
        </template>
      </p>
    </div>
  </section>
</template>
