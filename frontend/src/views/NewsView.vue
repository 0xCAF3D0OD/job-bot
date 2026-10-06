<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type NewsItem, type NewsPage, type NewsPreferences } from "../api/client";
import PageHero from "../components/PageHero.vue";
import { useNewsCount } from "../composables/useNewsCount";
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
let poll: ReturnType<typeof setTimeout> | undefined;
let polls = 0;

const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
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
    await api.POST("/api/news/seen");
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
  await api.PUT("/api/news/preferences", { body: preferences.value });
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
onUnmounted(() => clearTimeout(poll));
</script>

<template>
  <PageHero
    eyebrow="Actualités"
    title="Le marché de l'emploi, et de quoi progresser"
    subtitle="Articles récents sur l'emploi et vidéos choisies, filtrés selon ton domaine. Les sources se gèrent dans les Réglages."
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
            :title="hasDomain ? preferences.domain_keywords.join(' · ') : 'Définis ton domaine dans les Réglages'"
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
        <span class="news-status">
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
              Relever maintenant
            </button>
          </template>
        </span>
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
        v-else
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
    </div>
  </section>
</template>
