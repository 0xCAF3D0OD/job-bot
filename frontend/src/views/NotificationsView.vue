<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { InboxItem } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import FaceTransform from "../components/FaceTransform.vue";
import MoodAnimation from "../components/MoodAnimation.vue";
import NotificationCard from "../components/NotificationCard.vue";
import NotificationRow from "../components/NotificationRow.vue";
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

// « Toutes » et « Non lues » : un filtre, pas une navigation (LISEZMOI du 17.11, §48) : deux pastilles de 44 px,
// aria-pressed, comme les filtres du catalogue de formations.
const options = computed<{ value: "all" | "unread"; label: string; test: string }[]>(() => [
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
        <div
          class="notif-pills"
          role="group"
          aria-label="Filtre"
        >
          <button
            v-for="option in options"
            :key="option.value"
            type="button"
            class="notif-pill"
            :aria-pressed="filter === option.value"
            :data-test="option.test"
            @click="filter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
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
      <div
        v-if="!wide"
        class="notif-pills"
        role="group"
        aria-label="Filtre"
      >
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          class="notif-pill"
          :aria-pressed="filter === option.value"
          :data-test="option.test"
          @click="filter = option.value"
        >
          {{ option.label }}
        </button>
      </div>
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
        <!-- « Tout est lu » : sur téléphone, le Sourire de 140 px et son ombre (corrections du 13.11 au soir, §7 ;
             liseré clair en sombre) ; sur ordinateur, la cloche sonne dans l’arche, une fois (maquette Animations,
             NotificationsOrdinateur ne dessine pas cet état). Un seul des trois par écran. -->
        <div
          v-if="inbox.items.length && !wide"
          class="notifications-perso"
          data-test="notifications-perso"
        >
          <img
            class="notifications-sourire"
            src="/illustrations/sourire-pouce-140.webp"
            srcset="/illustrations/sourire-pouce-140.webp 1x, /illustrations/sourire-pouce-280.webp 2x"
            width="148"
            height="140"
            alt=""
            aria-hidden="true"
            decoding="async"
            data-test="notifications-sourire"
          >
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

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
/* §48 : pastille active à l'encre, inactive blanche au trait #DDD8CC (sombre #221E1A, trait #38322B). */
.notif-pills { --notif-pill-line: #DDD8CC; --notif-pill-pad: 16.5px; display: flex; gap: var(--space-2); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .notif-pills { --notif-pill-line: var(--line); } }
:root[data-theme="dark"] .notif-pills { --notif-pill-line: var(--line); }
.notif-pill {
  min-height: var(--target-min); padding: 0 var(--notif-pill-pad); border: 1.5px solid var(--notif-pill-line); border-radius: var(--radius-pill);
  background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-semibold); box-shadow: none;
}
.notif-pill:hover:not(:disabled) { background: var(--surface); box-shadow: none; }
.notif-pill[aria-pressed="true"], .notif-pill[aria-pressed="true"]:hover { border-color: var(--text); background: var(--text); color: var(--bg); font-weight: var(--weight-bold); }
.notifications-card li + li { border-top: 1px solid var(--line-soft); }
.notifications-head-wide .notifications-read-all { align-self: stretch; padding: 0 var(--space-1); font-size: var(--font-label); }
.notifications-wide .notifications-group { gap: var(--notif-10); }
.notifications-wide .notifications-group h2 { padding: 0 var(--space-1); font-size: var(--font-title); letter-spacing: normal; text-transform: none; color: var(--text); }
.notifications-wide .notifications-settings { justify-content: flex-start; justify-self: start; gap: var(--space-1); min-height: var(--target-min); font-size: var(--font-label); }
.notifications-families .notifications-group h2 { padding: 0; line-height: var(--space-4); letter-spacing: .06em; }
.notifications-page:not(.notifications-wide) .notifications-settings { min-height: var(--btn-tertiary); color: var(--primary-text); font-size: var(--font-label); }
@media (prefers-color-scheme: dark) {
:root:not([data-theme="light"]) .notifications-sourire { filter: drop-shadow(0 0 1px var(--text)) drop-shadow(0 0 1px var(--text)); }
}
:root[data-theme="dark"] .notifications-sourire { filter: drop-shadow(0 0 1px var(--text)) drop-shadow(0 0 1px var(--text)); }
@media (prefers-color-scheme: dark) {
:root:not([data-theme="light"]) .notifications-perso { --perso-shadow: rgb(0 0 0 / 35%); }
}
:root[data-theme="dark"] .notifications-perso { --perso-shadow: rgb(0 0 0 / 35%); }
@media (max-width: 820px) {
.notifications-page:not(.notifications-wide) { gap: var(--space-3); }
.notifications-page:not(.notifications-wide) .notifications-empty { --notif-empty-h: calc(100dvh - 168px); min-height: var(--notif-empty-h); box-sizing: border-box; align-content: center; padding: var(--space-6); }
.notifications-page:not(.notifications-wide) .notifications-empty [data-test=show-all] { min-height: var(--btn-secondary); margin-top: var(--space-2); padding: 0 var(--space-6); border-radius: var(--radius-pill); }
}
</style>
