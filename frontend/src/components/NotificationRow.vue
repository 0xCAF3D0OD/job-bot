<script setup lang="ts">
import { computed } from "vue";

import type { InboxItem } from "../api/client";
import { timeInList } from "../dates";
import { notificationKind } from "../notificationKinds";
import AppIcon from "./AppIcon.vue";
import NotificationIcon from "./NotificationIcon.vue";

// Une notification (maquette Notifications, N5 à N8) : l'icône du genre, le titre, l'heure et le point
// « non lue » sur la première ligne, le message dessous, puis le libellé de l'action. Toute la ligne est un
// seul lien, qui la marque lue et ouvre sa page ; le libellé n'en est que la partie visible, pas un bouton à
// part (décision du 2026-11-04). Sans page, un bouton qui la marque lue, sans libellé.
// `plain` (ordinateur, maquette du 8 novembre NotificationsOrdinateur) : sans icône (D23), le point « non lue » à
// gauche, l'heure à droite du titre, l'action en lien suivi d'un chevron.
const props = defineProps<{ item: InboxItem; plain?: boolean }>();
const emit = defineEmits<{ open: [item: InboxItem] }>();

const unread = computed(() => !props.item.read_at);
// Le message tient en une phrase ; un message sur plusieurs lignes (liste d'offres) garde sa première.
const text = computed(() => props.item.message?.split("\n")[0] ?? "");
const kind = computed(() => notificationKind(props.item.kind));
</script>

<template>
  <component
    :is="item.link ? 'RouterLink' : 'button'"
    v-bind="item.link ? { to: item.link } : { type: 'button' }"
    :class="['notif-row', { unread, 'notif-row-plain': plain }]"
    data-test="notification"
    @click="emit('open', item)"
  >
    <span
      v-if="plain"
      :class="['notif-row-mark', { on: unread }]"
      :role="unread ? 'img' : undefined"
      :aria-label="unread ? 'non lue' : undefined"
      :data-test="unread ? 'unread-dot' : undefined"
    />
    <NotificationIcon
      v-else
      :shape="kind.shape"
    />
    <span class="notif-row-body">
      <span class="notif-row-head">
        <strong class="notif-row-title">{{ item.title }}</strong>
        <span class="notif-row-time">
          {{ timeInList(item.created_at) }}<span
            v-if="unread && !plain"
            class="notif-row-dot"
            role="img"
            aria-label="non lue"
            data-test="unread-dot"
          />
        </span>
      </span>
      <span
        v-if="text"
        class="notif-row-text"
      >{{ text }}</span>
      <span
        v-if="item.link && kind.action"
        class="notif-row-action"
        data-test="notification-action"
      >{{ kind.action }}<AppIcon
        v-if="plain"
        name="chevron"
      /></span>
    </span>
  </component>
</template>
