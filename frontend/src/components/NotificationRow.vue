<script setup lang="ts">
import { computed } from "vue";

import type { InboxItem } from "../api/client";
import { timeInList } from "../dates";

// Une notification (maquette Notifications, N5 à N7) : le titre, l'heure et le point « non lue » sur la
// première ligne, le message dessous. Toute la ligne est un seul lien, qui la marque lue et ouvre sa page
// (décision du 2026-11-04) ; sans page, un bouton qui la marque lue.
const props = defineProps<{ item: InboxItem }>();
const emit = defineEmits<{ open: [item: InboxItem] }>();

const unread = computed(() => !props.item.read_at);
// Le message tient en une phrase ; un message sur plusieurs lignes (liste d'offres) garde sa première.
const text = computed(() => props.item.message?.split("\n")[0] ?? "");
</script>

<template>
  <component
    :is="item.link ? 'RouterLink' : 'button'"
    v-bind="item.link ? { to: item.link } : { type: 'button' }"
    :class="['notif-row', { unread }]"
    data-test="notification"
    @click="emit('open', item)"
  >
    <span class="notif-row-head">
      <strong class="notif-row-title">{{ item.title }}</strong>
      <span class="notif-row-time">
        {{ timeInList(item.created_at) }}<span
          v-if="unread"
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
  </component>
</template>
