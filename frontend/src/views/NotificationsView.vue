<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { InboxItem } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import FaceTransform from "../components/FaceTransform.vue";
import Illustration from "../components/Illustration.vue";
import MoodAnimation from "../components/MoodAnimation.vue";
import NotificationCard from "../components/NotificationCard.vue";
import NotificationRow from "../components/NotificationRow.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import { useInbox } from "../composables/useInbox";
import { usePhone } from "../composables/usePhone";
import { dayFamily, dayGroup } from "../dates";
import "../blocks.css";

// La page Notifications (maquette Notifications, docs/139 étape 9a ; décisions de Kevin du 2026-11-04) :
// retour à l'accueil, « Tout lire » (annulable 6 s), le filtre Toutes · Non lues, les notifications par
// jour, puis « Choisir mes notifications ». Sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.9) : les
// familles « Aujourd'hui », « Hier », « Plus tôt », une carte cliquable par notification, sans conteneur ; quand
// tout est lu, le personnage assis (perso-05-assis, 150 px de large) et son ombre ovale.
const { inbox, unread, refresh, markRead, readAll } = useInbox();
const filter = ref<"all" | "unread">("all");
// Ordinateur dès 1 024 px (maquette du 8 novembre, NotificationsOrdinateur) : le titre et les onglets sur une ligne,
// « Tout marquer comme lu », les jours en titres, les lignes sans icône.
const { phone } = usePhone();
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const wide = computed(() => wideQuery.value && !phone.value);

const options = computed(() => [
  { value: "all", label: "Toutes", test: "filter-all" },
  {
    value: "unread",
    label: unread.value ? (wide.value ? `Non lues · ${unread.value}` : `Non lues (${unread.value})`) : "Non lues",
    test: "filter-unread",
  },
]);
const shown = computed(() => inbox.value.items.filter((item) => filter.value === "all" || !item.read_at));
const groups = computed(() => {
  const found: { title: string; items: InboxItem[] }[] = [];
  for (const item of shown.value) {
    const title = wide.value ? dayGroup(item.created_at) : dayFamily(item.created_at);
    const group = found.find((g) => g.title === title);
    if (group) group.items.push(item);
    else found.push({ title, items: [item] });
  }
  return found;
});

onMounted(() => void refresh());
</script>

<template>
  <section class="band page-blocks-wide">
    <div
      :class="['container', 'notifications-page', { 'notifications-wide': wide }]"
      data-test="notifications"
    >
      <header
        v-if="wide"
        class="notifications-head-wide"
      >
        <h1>Notifications</h1>
        <SegmentedControl
          v-model="filter"
          :options="options"
          label="Vue"
        />
        <button
          type="button"
          class="notifications-read-all"
          :disabled="!unread"
          data-test="read-all"
          @click="readAll"
        >
          Tout marquer comme lu
        </button>
      </header>
      <header
        v-else
        class="notifications-head"
      >
        <RouterLink
          to="/"
          class="icon-button icon-only"
          aria-label="Retour à l’accueil"
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
        v-if="!wide"
        v-model="filter"
        :options="options"
        label="Afficher"
        full
      />
      <template v-if="groups.length">
        <template v-if="wide">
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
        </template>
        <div
          v-else
          class="blocks-page notifications-families"
        >
          <section
            v-for="(group, index) in groups"
            :key="group.title"
            class="notifications-group"
            :aria-labelledby="`notif-fam-${index}`"
          >
            <h2 :id="`notif-fam-${index}`">
              {{ group.title }}
            </h2>
            <ul class="notifications-list">
              <li
                v-for="item in group.items"
                :key="item.id"
              >
                <NotificationCard
                  :item="item"
                  @open="markRead"
                />
              </li>
            </ul>
          </section>
        </div>
        <RouterLink
          to="/reglages?rubrique=notifications"
          class="notifications-settings"
          data-test="notifications-settings"
        >
          Choisir mes notifications<AppIcon
            v-if="wide"
            name="chevron"
          />
        </RouterLink>
      </template>
      <div
        v-else
        class="face-state notifications-empty"
        role="status"
        data-test="notifications-empty"
      >
        <!-- « Tout est lu » : sur téléphone, le personnage assis et son ombre (§10.9, docs/141 §3) ; sur ordinateur,
             la cloche sonne dans l’arche, une fois (maquette Animations). Un seul des trois par écran. -->
        <div
          v-if="inbox.items.length && !wide"
          class="notifications-perso"
          data-test="notifications-perso"
        >
          <Illustration
            pose="assis"
            :height="211"
            full
          />
          <span
            class="notifications-perso-shadow"
            aria-hidden="true"
          />
        </div>
        <MoodAnimation
          v-else-if="inbox.items.length"
          kind="cloche"
        />
        <FaceTransform
          v-else
          kind="alerts"
          :size="120"
        />
        <h2 class="face-state-title">
          {{ inbox.items.length ? "Tout est lu" : "Aucune notification pour l’instant" }}
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
