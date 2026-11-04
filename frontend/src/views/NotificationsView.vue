<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { InboxItem } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import FaceTransform from "../components/FaceTransform.vue";
import NotificationRow from "../components/NotificationRow.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import { useInbox } from "../composables/useInbox";
import { dayGroup } from "../dates";

// La page Notifications (maquette Notifications, docs/139 étape 9a ; décisions de Kevin du 2026-11-04) :
// retour à l'accueil, « Tout lire » (annulable 6 s), le filtre Toutes · Non lues, les notifications par
// jour, chaque groupe dans une carte, puis « Choisir mes notifications ».
const { inbox, unread, refresh, markRead, readAll } = useInbox();
const filter = ref<"all" | "unread">("all");

const options = computed(() => [
  { value: "all", label: "Toutes", test: "filter-all" },
  { value: "unread", label: unread.value ? `Non lues (${unread.value})` : "Non lues", test: "filter-unread" },
]);
const shown = computed(() => inbox.value.items.filter((item) => filter.value === "all" || !item.read_at));
const groups = computed(() => {
  const found: { title: string; items: InboxItem[] }[] = [];
  for (const item of shown.value) {
    const title = dayGroup(item.created_at);
    const group = found.find((g) => g.title === title);
    if (group) group.items.push(item);
    else found.push({ title, items: [item] });
  }
  return found;
});

onMounted(() => void refresh());
</script>

<template>
  <section class="band">
    <div
      class="container notifications-page"
      data-test="notifications"
    >
      <header class="notifications-head">
        <RouterLink
          to="/"
          class="icon-button icon-only"
          aria-label="Retour à l'accueil"
          data-test="notifications-back"
        >
          <AppIcon name="arrow-left" />
        </RouterLink>
        <h1>Notifications</h1>
        <button
          type="button"
          class="notifications-read-all"
          :disabled="!unread"
          data-test="read-all"
          @click="readAll"
        >
          Tout lire
        </button>
      </header>
      <SegmentedControl
        v-model="filter"
        :options="options"
        label="Afficher"
        full
      />
      <template v-if="groups.length">
        <section
          v-for="group in groups"
          :key="group.title"
          class="notifications-group"
        >
          <h2>{{ group.title }}</h2>
          <ul class="notifications-card">
            <li
              v-for="item in group.items"
              :key="item.id"
            >
              <NotificationRow
                :item="item"
                @open="markRead"
              />
            </li>
          </ul>
        </section>
        <RouterLink
          to="/reglages?rubrique=notifications"
          class="notifications-settings"
          data-test="notifications-settings"
        >
          Choisir mes notifications
        </RouterLink>
      </template>
      <div
        v-else
        class="face-state notifications-empty"
        role="status"
        data-test="notifications-empty"
      >
        <FaceTransform
          kind="alerts"
          :size="120"
        />
        <h2 class="face-state-title">
          {{ inbox.items.length ? "Tout est lu" : "Aucune notification pour l'instant" }}
        </h2>
        <p class="face-state-line">
          Les nouvelles offres et les rappels ORP arriveront ici.
        </p>
        <button
          v-if="inbox.items.length"
          type="button"
          class="secondary"
          data-test="show-all"
          @click="filter = 'all'"
        >
          Voir toutes les notifications
        </button>
      </div>
    </div>
  </section>
</template>
