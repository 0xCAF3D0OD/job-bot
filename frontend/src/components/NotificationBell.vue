<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type Inbox, type InboxItem } from "../api/client";
import { dateInList } from "../dates";
import { plural } from "../format";
import { useNarrow } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

// Cloche des alertes (docs/15 §1) : les mêmes que sur le téléphone, relues chaque minute.
const REFRESH_MS = 60_000;

const router = useRouter();
const inbox = ref<Inbox>({ unread: 0, items: [] });
// Un bouton rond, sans capsule (1.6.46) : le menu s'ouvre sous lui.
const open = ref(false);
const root = ref<HTMLElement | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;
// Sous 600 px (planche « Structure téléphone ») : la cloche s'ouvre en feuille plein écran, titre à gauche et
// ✕ rond à droite ; au-delà, le panneau sous le bouton.
const { phone: narrow } = useNarrow();
const unread = computed(() => inbox.value.items.filter((i) => !i.read_at));
const read = computed(() => inbox.value.items.filter((i) => i.read_at));

const badge = computed(() => (inbox.value.unread > 9 ? "9+" : String(inbox.value.unread)));
const label = computed(() =>
  inbox.value.unread ? `Alertes, ${plural(inbox.value.unread, "non lue", "non lues")}` : "Alertes",
);

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
  // Le panneau et la feuille sont dans la cloche : un clic ailleurs la ferme.
  if (open.value && !root.value?.contains(target)) open.value = false;
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
    <!-- Sans alerte : un rond neutre ; avec des alertes : une capsule orange clair, la cloche et le
         chiffre côte à côte (1.6.46). La légende reprend le nom accessible (WCAG 1.4.13). -->
    <button
      type="button"
      :class="['header-round', 'bell-button', { 'has-unread': inbox.unread }]"
      :aria-label="label"
      :data-label="label"
      :aria-expanded="open"
      data-test="bell"
      @click="toggle"
    >
      <AppIcon name="bell" />
      <span
        v-if="inbox.unread"
        class="bell-count"
        aria-hidden="true"
        data-test="bell-badge"
      >{{ badge }}</span>
    </button>
    <component
      :is="narrow ? BottomSheet : 'div'"
      v-if="narrow || open"
      v-bind="narrow ? { open, title: 'Alertes', full: true } : { class: 'bell-panel', role: 'dialog', 'aria-label': 'Alertes' }"
      data-test="bell-panel"
      @close="open = false"
    >
      <div class="bell-head">
        <strong v-if="!narrow">Alertes</strong>
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
      <!-- Sur téléphone, deux listes groupées : les nouvelles, puis celles déjà lues (planche). -->
      <template v-else-if="narrow">
        <GroupedList
          v-for="group in [{ title: 'Nouvelles', items: unread }, { title: 'Déjà lues', items: read }].filter((g) => g.items.length)"
          :key="group.title"
          :title="group.title"
          :level="3"
        >
          <GroupedRow
            v-for="item in group.items"
            :key="item.id"
            :title="item.title"
            :description="item.message?.split('\n')[0] ?? ''"
            :value="dateInList(item.created_at)"
            :class="{ 'bell-unread': !item.read_at }"
            button
            :chevron="Boolean(item.link)"
            data-test="bell-item"
            @click="select(item)"
          />
        </GroupedList>
      </template>
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
            <span class="bell-time">{{ dateInList(item.created_at) }}</span>
          </button>
        </li>
      </ul>
    </component>
  </div>
</template>
