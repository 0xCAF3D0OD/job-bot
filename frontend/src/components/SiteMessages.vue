<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { api } from "../api/client";
import { sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

// Les messages des sites (docs/112) : ce que les sites écrivent à l'adresse jobA1 de la
// personne et qui n'est pas une alerte (bienvenue, alerte modifiée, mot de passe oublié),
// gardés 30 jours. Le texte se charge à l'ouverture, sans images.
type SiteMessage = { id: number; site: string; subject?: string | null; received_at: string };
const items = ref<SiteMessage[]>([]);
const openId = ref<number | null>(null);
const texts = reactive<Record<number, string>>({});
const day = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short", timeZone: "Europe/Zurich" });

// Un message ouvert à la fois ; le texte se charge la première fois.
async function toggle(item: SiteMessage): Promise<void> {
  openId.value = openId.value === item.id ? null : item.id;
  if (openId.value === null || item.id in texts) return;
  const { data } = await api.GET("/api/alert-searches/messages/{search_id}", { params: { path: { search_id: item.id } } });
  texts[item.id] = data?.text || "Ce message n'a pas de texte.";
}

onMounted(async () => {
  const { data } = await api.GET("/api/alert-searches/messages");
  if (Array.isArray(data)) items.value = data;
});
</script>

<template>
  <section
    v-if="items.length"
    class="site-messages"
    data-test="site-messages"
  >
    <h2 class="section-title first">
      Messages des sites
    </h2>
    <p class="setting-desc">
      Ce que les sites t'écrivent et qui n'est pas une alerte, gardé 30 jours.
    </p>
    <ul class="settings-card site-message-list">
      <li
        v-for="item in items"
        :key="item.id"
        data-test="site-message"
      >
        <button
          type="button"
          class="site-message-row"
          :aria-expanded="openId === item.id"
          @click="toggle(item)"
        >
          <span class="site-message-head">
            <strong>{{ item.subject || "Sans sujet" }}</strong>
            <span class="site-message-meta">{{ item.site === "unknown" ? "un site" : sourceLabel[item.site] }} · {{ day.format(new Date(item.received_at)) }}</span>
          </span>
          <AppIcon
            name="chevron"
            class="site-message-chevron"
          />
        </button>
        <p
          v-if="openId === item.id"
          class="site-message-text"
        >
          {{ texts[item.id] ?? "…" }}
        </p>
      </li>
    </ul>
  </section>
</template>
