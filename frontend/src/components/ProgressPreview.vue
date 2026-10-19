<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, BACKGROUND, type NewsItem, type Training } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { CAPSULE_BODY, useCapsuleZone } from "../composables/useCapsule";
import { useNewsCount } from "../composables/useNewsCount";
import AppIcon from "./AppIcon.vue";

// Progresser dans la capsule (docs/92) : le livre (docs/101), entre la cloche et ton initiale, déroule
// un aperçu — les dernières actualités de ton domaine et tes formations en cours. Un point
// violet dit qu'il y a du nouveau à lire ; il s'efface quand on ouvre l'aperçu.
const route = useRoute();
const { me } = useAuth();
const { open, inCapsule } = useCapsuleZone("progress");
const { count, reset } = useNewsCount();
const news = ref<NewsItem[]>([]);
const trainings = ref<Training[]>([]);
const loaded = ref(false);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

const active = computed(() => route.path.startsWith("/progresser"));
const label = computed(() => (count.value ? "Progresser, du nouveau à lire" : "Progresser"));

// Comme la carte d'Aujourd'hui : les dernières du domaine ; à défaut, celles sur l'emploi.
async function loadNews(): Promise<void> {
  const mine = await api.GET("/api/news", { params: { query: { kind: "articles", limit: 3, domain_only: true } } });
  const items = (mine.data?.items ?? []).filter((item) => item.matched.length);
  if (items.length) {
    news.value = items;
    return;
  }
  const jobs = await api.GET("/api/news", { params: { query: { kind: "articles", limit: 3, topic: "jobs" } } });
  news.value = jobs.data?.items ?? [];
}

async function loadTrainings(): Promise<void> {
  const { data } = await api.GET("/api/trainings", { params: { query: { domain_only: false } } });
  trainings.value = (data?.items ?? []).filter((t) => t.mark?.status === "in_progress").slice(0, 3);
}

async function markSeen(): Promise<void> {
  if (!count.value) return;
  reset();
  if (!me.value?.demo) await api.POST("/api/news/seen", BACKGROUND).catch(() => undefined);
}

watch(open, async (isOpen) => {
  if (!isOpen) return;
  void markSeen();
  await Promise.all([loadNews().catch(() => undefined), loadTrainings().catch(() => undefined)]);
  loaded.value = true;
});

function close(): void {
  open.value = false;
}
</script>

<template>
  <div class="progress-zone">
    <button
      type="button"
      :class="['capsule-zone', 'progress-trigger', { active }]"
      data-capsule-zone="progress"
      :aria-expanded="open"
      :aria-label="label"
      data-test="progress-zone"
      @click="open = !open"
    >
      <AppIcon name="book" />
      <span
        v-if="count"
        class="progress-dot"
        data-test="progress-dot"
      />
    </button>
    <Teleport
      :to="CAPSULE_BODY"
      defer
      :disabled="!inCapsule"
    >
      <div
        v-if="open"
        class="progress-preview"
        role="dialog"
        aria-label="Progresser"
        data-test="progress-preview"
      >
        <p class="preview-title">
          <span class="with-icon"><AppIcon name="news" />Actualités</span>
        </p>
        <ul
          v-if="news.length"
          class="preview-news"
        >
          <li
            v-for="item in news"
            :key="item.id"
          >
            <a
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              data-test="preview-news"
            >
              <span :class="['preview-thumb', { text: !item.has_image }]">
                <img
                  v-if="item.has_image"
                  :src="`/api/news/items/${item.id}/image`"
                  alt=""
                  loading="lazy"
                >
              </span>
              <span>
                <strong>{{ item.title }}</strong>
                <span class="muted">{{ item.source }} · {{ longDate.format(new Date(item.published_at)) }}</span>
              </span>
            </a>
          </li>
        </ul>
        <p
          v-else-if="loaded"
          class="muted preview-empty"
        >
          Rien de nouveau pour l'instant.
        </p>
        <template v-if="trainings.length">
          <p class="preview-title">
            <span class="with-icon"><AppIcon name="book" />Formations en cours</span>
          </p>
          <ul
            class="preview-trainings"
            data-test="preview-trainings"
          >
            <li
              v-for="training in trainings"
              :key="training.id"
            >
              <RouterLink
                :to="{ path: '/progresser/formations', query: { onglet: 'miennes', formation: String(training.id) } }"
                @click="close"
              >
                <strong>{{ training.title }}</strong>
                <span class="muted">{{ training.mark?.progress || "En cours" }} · {{ training.provider }}</span>
              </RouterLink>
            </li>
          </ul>
        </template>
        <div class="preview-links">
          <RouterLink
            to="/progresser/actualites"
            data-test="preview-all-news"
            @click="close"
          >
            Toutes les actualités
          </RouterLink>
          <RouterLink
            to="/progresser/formations"
            data-test="preview-all-trainings"
            @click="close"
          >
            Toutes les formations
          </RouterLink>
        </div>
      </div>
    </Teleport>
  </div>
</template>
