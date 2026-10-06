<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type NewsItem } from "../api/client";
import PageHero from "../components/PageHero.vue";
import { useNewsCount } from "../composables/useNewsCount";

// Actualités (docs/15 §2) : marché de l'emploi et vidéos, depuis des flux publics.
const route = useRoute();
const tab = computed<"articles" | "videos">(() => (route.query.rubrique === "videos" ? "videos" : "articles"));
const items = ref<NewsItem[]>([]);
const counts = ref({ articles: 0, videos: 0 });
const loaded = ref(false);
const { reset } = useNewsCount();

const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

async function load(): Promise<void> {
  const { data } = await api.GET("/api/news", { params: { query: { kind: tab.value, limit: 60 } } });
  items.value = data?.items ?? [];
  if (data && !loaded.value) {
    counts.value = { articles: data.new_articles, videos: data.new_videos };
    // La visite remet les compteurs à zéro (pour la prochaine fois).
    await api.POST("/api/news/seen");
    reset();
  }
  loaded.value = true;
}

watch(tab, () => void load());
onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Actualités"
    title="Le marché de l'emploi, et de quoi progresser"
    subtitle="Articles récents sur l'emploi en Suisse et vidéos choisies. Les sources se gèrent dans les Réglages."
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

      <p
        v-if="loaded && !items.length"
        class="muted empty"
      >
        Rien pour l'instant : les sources sont relevées toutes les 6 heures.
        <RouterLink to="/reglages#actualites">
          Gérer les sources
        </RouterLink>
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
              <strong class="news-title">{{ item.title }}</strong>
              <span
                v-if="item.summary"
                class="news-summary"
              >{{ item.summary }}</span>
            </span>
          </a>
        </li>
      </ul>
    </div>
  </section>
</template>
