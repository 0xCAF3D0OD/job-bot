<script setup lang="ts">
import { computed } from "vue";

import type { InboxItem } from "../api/client";
import { timeInCard } from "../dates";
import { notificationKind } from "../notificationKinds";
import AppIcon from "./AppIcon.vue";

// Une notification sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.9 ; maquettes Notifications et
// NotificationsSombre) : une carte cliquable (D29), un seul arrêt de tabulation. L'icône du type (24 px, sans fond),
// le titre (700 non lue, 500 lue), la description seulement si le message en a une (sa première ligne), puis la
// ligne d'information : « Non lue » après un point bleu (la couleur n'est jamais le seul repère), « · » et l'heure.
// Le cercle à flèche est décoratif. Toucher la carte la marque lue et ouvre sa page ; sans page, elle la marque lue.
const props = defineProps<{ item: InboxItem }>();
const emit = defineEmits<{ open: [item: InboxItem] }>();

const unread = computed(() => !props.item.read_at);
const text = computed(() => props.item.message?.split("\n")[0] ?? "");
const kind = computed(() => notificationKind(props.item.kind));
</script>

<template>
  <component
    :is="item.link ? 'RouterLink' : 'button'"
    v-bind="item.link ? { to: item.link } : { type: 'button' }"
    :class="['block-row', 'notif-card', { unread }]"
    data-test="notification"
    @click="emit('open', item)"
  >
    <span
      :class="['notif-card-icon', { late: kind.late }]"
      :data-icon="kind.icon"
    ><AppIcon :name="kind.icon" /></span>
    <span class="block-row-text">
      <span class="notif-card-title">{{ item.title }}</span>
      <span
        v-if="text"
        class="notif-card-text"
      ><span class="visually-hidden">, </span>{{ text }}</span>
      <span class="notif-card-info">
        <template v-if="unread">
          <span
            class="notif-card-dot"
            aria-hidden="true"
            data-test="unread-dot"
          />
          <span class="notif-card-unread"><span class="visually-hidden">, </span>Non lue</span>
          <span aria-hidden="true">·</span>
        </template>
        <span><span class="visually-hidden">, </span>{{ timeInCard(item.created_at) }}</span>
      </span>
    </span>
    <span
      class="arrow-circle"
      aria-hidden="true"
    ><AppIcon name="arrow-right" /></span>
  </component>
</template>

<style>
/* Valeurs du HTML de Notifications : carte de 72 px au moins, 18,5 px de marge intérieure (avec la bordure de
   1,5 px), 16 px entre les colonnes ; titre 16/22, description 14/20 et information 13/16, 4 px entre elles. */
/* Le titre d'une notification lue : 500, valeur de la maquette (pas de jeton). */
.notif-card { --notif-read: 500; }
.notif-card .notif-card-icon { display: flex; flex: none; color: var(--primary-graphic); }
.notif-card .notif-card-icon.late { color: var(--peach-text); }
.notif-card .notif-card-icon .icon { width: 24px; height: 24px; }
.notif-card-title { font-size: var(--font-body); line-height: var(--row-title-lh); font-weight: var(--notif-read); color: var(--text); overflow-wrap: anywhere; }
.notif-card.unread .notif-card-title { font-weight: var(--weight-bold); }
.notif-card-text { margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--row-line-lh); color: var(--text-secondary); overflow-wrap: anywhere; }
.notif-card-info { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-1); font-size: var(--label-caps); line-height: var(--space-4); color: var(--text-secondary); }
.notif-card-dot { flex: none; width: 8px; height: 8px; border-radius: var(--radius-pill); background: var(--primary-graphic); }
.notif-card-unread { font-weight: var(--weight-bold); color: var(--primary-text); }
</style>
