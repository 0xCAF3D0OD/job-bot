<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type NewsItem, type NewsPage, type NewsPreferences } from "../api/client";
import HelpTip from "../components/HelpTip.vue";
import PushTransition from "../components/PushTransition.vue";
import PageHero from "../components/PageHero.vue";
import { useAuth } from "../composables/useAuth";
import { useNewsCount } from "../composables/useNewsCount";
import { usePhone } from "../composables/usePhone";
import { since } from "../format";
import { countryLabel, highlight, languageLabel } from "../newsLabels";

// Actualités (docs/15 §2, docs/16) : marché de l'emploi et vidéos, filtrés selon ton domaine.
const POLL_MS = 4_000;
const POLL_LIMIT = 30; // deux minutes au plus

const route = useRoute();
const tab = computed<"articles" | "videos">(() => (route.query.rubrique === "videos" ? "videos" : "articles"));
const items = ref<NewsItem[]>([]);
const page = ref<NewsPage | null>(null);
const preferences = ref<NewsPreferences | null>(null);
const counts = ref({ articles: 0, videos: 0 });
const loaded = ref(false);
const { reset } = useNewsCount();
const { loggedIn } = useAuth();
let poll: ReturnType<typeof setTimeout> | undefined;
let polls = 0;

const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

// Page « journal » (docs/32 §5) : un article à la une, puis des titres seuls groupés par
// période ; les vidéos gardent leurs cartes (la vignette y est l'information).
const lead = computed(() => (tab.value === "articles" ? (items.value[0] ?? null) : null));
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
  const rest = items.value.slice(1);
  return PERIODS.map((p) => ({ ...p, items: rest.filter((item) => period(item.published_at) === p.key) })).filter(
    (g) => g.items.length,
  );
});

// « SECO — marché du travail » : le nom court suffit sur une ligne de titre.
function shortSource(source: string): string {
  return source.split(" — ")[0] ?? source;
}

// Pays et langue derrière « Filtrer » (docs/32 §5.2), avec le nombre de filtres actifs.
const filtersOpen = ref(false);
const filtersRoot = ref<HTMLElement | null>(null);
// Téléphone (retour du 2026-10-15) : comme les alertes, une carte sur toute la largeur sous
// la ligne des filtres, qui pousse la liste en douceur. Ordinateur : le menu déroulant.
const filtersPopover = ref<HTMLElement | null>(null);
const { phone } = usePhone();
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

async function load(): Promise<void> {
  const prefs = preferences.value;
  const { data } = await api.GET("/api/news", {
    params: {
      query: {
        kind: tab.value,
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
    counts.value = { articles: data.new_articles, videos: data.new_videos };
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

watch(tab, () => void load());
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
    eyebrow="Actualités"
    title="Le marché de l'emploi, et de quoi progresser"
    subtitle="L'emploi et ton domaine : articles et vidéos récents."
  />
  <section class="band">
    <div class="container">
      <nav
        class="prep-tabs"
        aria-label="Actualités"
      >
        <RouterLink
          :to="{ query: {} }"
          :class="{ active: tab === 'articles' }"
          data-test="tab-articles"
        >
          Marché de l'emploi
          <span
            v-if="counts.articles"
            class="tab-count"
          >{{ counts.articles }}</span>
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
            :disabled="!hasDomain"
            data-test="filter-domain"
            @click="savePreferences({ domain_only: true })"
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
        <HelpTip
          v-if="hasDomain"
          :text="`Mon domaine : ${preferences.domain_keywords.join(', ')}. À modifier dans Réglages › Actualités.`"
          label="Mots de Mon domaine"
        />
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
      <p
        v-if="preferences && !hasDomain"
        class="hint"
      >
        Pour filtrer selon ton domaine (DevOps, Kubernetes…), indique tes mots-clés dans
        <RouterLink to="/reglages#actualites">
          Réglages → Actualités
        </RouterLink>.
      </p>

      <p
        v-if="loaded && !items.length"
        class="muted empty"
      >
        <template v-if="page?.refreshing">
          Premier relevé en cours : les contenus arrivent dans quelques secondes.
        </template>
        <template v-else-if="preferences?.domain_only || preferences?.countries.length || preferences?.languages.length">
          Rien avec ces filtres pour l'instant.
        </template>
        <template v-else>
          Rien pour l'instant.
          <RouterLink to="/reglages#actualites">
            Gérer les sources
          </RouterLink>
        </template>
      </p>
      <ul
        v-else-if="tab === 'videos'"
        :class="['news-grid', tab]"
      >
        <li
          v-for="item in items"
          :key="item.id"
        >
          <a
            class="news-card"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            data-test="news-item"
          >
            <img
              v-if="item.has_image"
              class="news-image"
              :src="`/api/news/items/${item.id}/image`"
              alt=""
              loading="lazy"
            >
            <span class="news-body">
              <span class="news-meta">{{ item.source }} · {{ dateFormat.format(new Date(item.published_at)) }}</span>
              <strong class="news-title"><template
                v-for="(part, index) in highlight(item.title, item.matched)"
                :key="index"
              ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></strong>
              <span
                v-if="item.summary"
                class="news-summary"
              ><template
                v-for="(part, index) in highlight(item.summary, item.matched)"
                :key="index"
              ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
            </span>
          </a>
        </li>
      </ul>
      <div
        v-else
        class="news-journal"
      >
        <a
          v-if="lead"
          class="news-lead"
          :href="lead.url"
          target="_blank"
          rel="noopener noreferrer"
          data-test="news-item"
        >
          <img
            v-if="lead.has_image"
            class="news-image"
            :src="`/api/news/items/${lead.id}/image`"
            alt=""
            loading="lazy"
          >
          <span class="news-body">
            <span class="news-meta">À la une · {{ lead.source }} · {{ dateFormat.format(new Date(lead.published_at)) }}</span>
            <strong class="news-title news-lead-title"><template
              v-for="(part, index) in highlight(lead.title, lead.matched)"
              :key="index"
            ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></strong>
            <span
              v-if="lead.summary"
              class="news-summary"
            ><template
              v-for="(part, index) in highlight(lead.summary, lead.matched)"
              :key="index"
            ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
          </span>
        </a>
        <section
          v-for="group in groups"
          :key="group.key"
          class="news-group"
        >
          <h2 class="news-group-title">
            {{ group.label }}
          </h2>
          <ul class="news-rows">
            <li
              v-for="item in group.items"
              :key="item.id"
            >
              <a
                class="news-row"
                :href="item.url"
                target="_blank"
                rel="noopener noreferrer"
                data-test="news-item"
              >
                <span class="news-row-main">
                  <span class="news-title"><template
                    v-for="(part, index) in highlight(item.title, item.matched)"
                    :key="index"
                  ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
                  <span
                    v-if="item.summary"
                    class="news-row-summary"
                  >{{ item.summary }}</span>
                </span>
                <span class="news-row-meta">{{ shortSource(item.source) }} · {{ shortDate.format(new Date(item.published_at)) }}</span>
              </a>
            </li>
          </ul>
        </section>
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
