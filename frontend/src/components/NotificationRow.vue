<script setup lang="ts">
import { computed } from "vue";

import type { InboxItem } from "../api/client";
import { timeInList } from "../dates";
import { notificationKind } from "../notificationKinds";
import AppIcon from "./AppIcon.vue";

// Une notification sur ordinateur (maquette du 8 novembre, NotificationsOrdinateur) : sans icône (D23), le point
// « non lue » à gauche, le titre et l'heure à sa droite, le message dessous, puis le libellé de l'action suivi d'un
// chevron. Toute la ligne est un seul lien, qui la marque lue et ouvre sa page (décision du 2026-11-04). Sans page,
// un bouton qui la marque lue, sans libellé. Sur téléphone : NotificationCard (§10.9).
const props = defineProps<{ item: InboxItem }>();
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
    :class="['notif-row', 'notif-row-plain', { unread }]"
    data-test="notification"
    @click="emit('open', item)"
  >
    <span
      :class="['notif-row-mark', { on: unread }]"
      :role="unread ? 'img' : undefined"
      :aria-label="unread ? 'non lue' : undefined"
      :data-test="unread ? 'unread-dot' : undefined"
    />
    <span class="notif-row-body">
      <span class="notif-row-head">
        <strong class="notif-row-title">{{ item.title }}</strong>
        <span class="notif-row-time">{{ timeInList(item.created_at) }}</span>
      </span>
      <span
        v-if="text"
        class="notif-row-text"
      >{{ text }}</span>
      <span
        v-if="item.link && kind.action"
        class="notif-row-action"
        data-test="notification-action"
      >{{ kind.action }}<AppIcon name="chevron" /></span>
    </span>
  </component>
</template>
