<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type Inbox, type InboxItem } from "../api/client";
import { plural, since } from "../format";
import AppIcon from "./AppIcon.vue";
import { CAPSULE_BODY, useCapsuleZone } from "../composables/useCapsule";
import CountBadge from "./CountBadge.vue";

// Cloche des alertes (docs/15 §1) : les mêmes que sur le téléphone, relues chaque minute.
const REFRESH_MS = 60_000;

const router = useRouter();
const inbox = ref<Inbox>({ unread: 0, items: [] });
// Dans la capsule (docs/91), une seule chose ouverte à la fois : la cloche ou le compte.
const { open, inCapsule } = useCapsuleZone("bell");
const root = ref<HTMLElement | null>(null);
// Elle se déroule dans la capsule (docs/91) ; sur téléphone, la capsule l'ouvre en plein écran
// sous l'en-tête, comme Sphere (docs/109).
const panel = ref<HTMLElement | null>(null);
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
  const target = event.target as Node;
  if (open.value && !root.value?.contains(target) && !panel.value?.contains(target)) open.value = false;
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
      class="bell-button capsule-zone"
      data-capsule-zone="bell"
      :aria-label="inbox.unread ? `Alertes, ${plural(inbox.unread, 'non lue', 'non lues')}` : 'Alertes'"
      :aria-expanded="open"
      data-test="bell"
      @click="toggle"
    >
      <AppIcon name="bell" />
      <CountBadge
        v-if="inbox.unread"
        class="bell-badge"
        data-test="bell-badge"
        tone="orange"
        :count="badge"
      />
    </button>
    <Teleport
      :to="CAPSULE_BODY"
      defer
      :disabled="!inCapsule"
    >
      <div
        v-if="open"
        ref="panel"
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
            <span class="with-icon"><AppIcon name="done" />Tout marquer comme lu</span>
          </button>
        </div>
        <p
          v-if="!inbox.items.length"
          class="hint bell-empty"
        >
          Aucune alerte pour l'instant.
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
    </Teleport>
  </div>
</template>
