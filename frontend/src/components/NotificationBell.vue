<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type Inbox, type InboxItem } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Cloche des alertes (docs/15 §1) : les mêmes que sur le téléphone, relues chaque minute.
const REFRESH_MS = 60_000;

const router = useRouter();
const inbox = ref<Inbox>({ unread: 0, items: [] });
const open = ref(false);
const root = ref<HTMLElement | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;

const badge = computed(() => (inbox.value.unread > 9 ? "9+" : String(inbox.value.unread)));

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/inbox");
    if (data) inbox.value = data;
  } catch {
    // API momentanément injoignable : on réessaiera à la prochaine minute.
  }
}

function since(iso: string): string {
  const minutes = Math.max(0, Math.round((Date.now() - Date.parse(iso)) / 60_000));
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `il y a ${hours} h`;
  const days = Math.round(hours / 24);
  return days === 1 ? "hier" : `il y a ${days} jours`;
}

async function select(item: InboxItem): Promise<void> {
  open.value = false;
  if (!item.read_at) {
    const { data } = await api.POST("/api/inbox/{notification_id}/read", {
      params: { path: { notification_id: item.id } },
    });
    if (data) inbox.value = data;
  }
  if (item.link) await router.push(item.link);
}

function toggle(): void {
  open.value = !open.value;
  if (open.value) void refresh();
}

async function readAll(): Promise<void> {
  const { data } = await api.POST("/api/inbox/read-all");
  if (data) inbox.value = data;
}

function onDocumentClick(event: MouseEvent): void {
  if (open.value && root.value && !root.value.contains(event.target as Node)) open.value = false;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") open.value = false;
}

onMounted(() => {
  void refresh();
  timer = setInterval(() => void refresh(), REFRESH_MS);
  document.addEventListener("click", onDocumentClick);
  document.addEventListener("keydown", onKeydown);
});
onUnmounted(() => {
  clearInterval(timer);
  document.removeEventListener("click", onDocumentClick);
  document.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <div
    ref="root"
    class="bell"
  >
    <button
      type="button"
      class="bell-button"
      :aria-label="inbox.unread ? `Alertes, ${inbox.unread} non lue(s)` : 'Alertes'"
      :aria-expanded="open"
      data-test="bell"
      @click="toggle"
    >
      <AppIcon name="bell" />
      <span
        v-if="inbox.unread"
        class="bell-badge"
        data-test="bell-badge"
      >{{ badge }}</span>
    </button>
    <div
      v-if="open"
      class="bell-panel"
      role="dialog"
      aria-label="Alertes"
      data-test="bell-panel"
    >
      <div class="bell-head">
        <strong>Alertes</strong>
        <button
          v-if="inbox.unread"
          type="button"
          class="link"
          data-test="read-all"
          @click="readAll"
        >
          Tout marquer comme lu
        </button>
      </div>
      <p
        v-if="!inbox.items.length"
        class="hint bell-empty"
      >
        Aucune alerte pour l'instant. Les bonnes offres, les relances et les rappels ORP apparaîtront ici.
      </p>
      <ul v-else>
        <li
          v-for="item in inbox.items"
          :key="item.id"
        >
          <button
            type="button"
            :class="['bell-item', { unread: !item.read_at }]"
            data-test="bell-item"
            @click="select(item)"
          >
            <span class="bell-title">{{ item.title }}</span>
            <span
              v-if="item.message"
              class="bell-text"
            >{{ item.message.split("\n")[0] }}</span>
            <span class="bell-time">{{ since(item.created_at) }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
