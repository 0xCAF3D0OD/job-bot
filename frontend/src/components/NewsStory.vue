<script setup lang="ts">
import type { NewsItem } from "../api/client";
import { since } from "../format";
import { highlight } from "../newsLabels";

// Une actualité à la manière de RTS (docs/35) : l'image (ou une vignette texte), la source en
// petit, le titre, l'heure. Trois tailles : en tête, second rang, ligne.
defineProps<{ item: NewsItem; variant: "lead" | "second" | "row" }>();

// « SECO — marché du travail » : le nom court suffit.
function shortSource(source: string): string {
  return source.split(" — ")[0] ?? source;
}
</script>

<template>
  <a
    :class="['news-story', variant]"
    :href="item.url"
    target="_blank"
    rel="noopener noreferrer"
    data-test="news-item"
  >
    <span :class="['news-thumb', { text: !item.has_image }]">
      <img
        v-if="item.has_image"
        :src="`/api/news/items/${item.id}/image`"
        alt=""
        loading="lazy"
      >
      <span v-else>{{ shortSource(item.source) }}</span>
      <span
        v-if="item.kind === 'videos'"
        class="news-play"
        aria-hidden="true"
      >▶</span>
    </span>
    <span class="news-story-body">
      <span class="news-kicker">{{ shortSource(item.source) }}</span>
      <strong class="news-title news-story-title"><template
        v-for="(part, index) in highlight(item.title, item.matched)"
        :key="index"
      ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></strong>
      <span class="news-time">{{ since(item.published_at) }}</span>
    </span>
  </a>
</template>
