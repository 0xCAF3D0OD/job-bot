<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import type { InboxItem } from "../api/client";
import { plural } from "../format";
import { useInbox } from "../composables/useInbox";
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import NotificationRow from "./NotificationRow.vue";

// Cloche des notifications (docs/15 §1 ; « Notifications » et non « Alertes », le nom de l'onglet des
// sources d'offres dans Candidatures), relue chaque minute. Sur téléphone, elle mène à la page
// /notifications (maquette Notifications) ; sur ordinateur, elle ouvre son panneau, avec les mêmes lignes
// que la page et « Tout voir » (N2, décision du 2026-11-04).
const REFRESH_MS = 60_000;
// Le panneau montre les plus récentes ; la page, toutes.
const PANEL_MAX = 8;

const { inbox, refresh, markRead, readAll } = useInbox();
const open = ref(false);
const root = ref<HTMLElement | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;
const { phone } = usePhone();
const recent = computed(() => inbox.value.items.slice(0, PANEL_MAX));

const badge = computed(() => (inbox.value.unread > 9 ? "9+" : String(inbox.value.unread)));
const label = computed(() =>
  inbox.value.unread ? `Notifications, ${plural(inbox.value.unread, "non lue", "non lues")}` : "Notifications",
);

function select(item: InboxItem): void {
  open.value = false;
  void markRead(item);
}

function toggle(): void {
  open.value = !open.value;
  if (open.value) void refresh();
}

function onDocumentClick(event: MouseEvent): void {
  // Le panneau est dans la cloche : un clic ailleurs le ferme.
  if (open.value && !root.value?.contains(event.target as Node)) open.value = false;
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
    <component
      :is="phone ? 'RouterLink' : 'button'"
      v-bind="phone ? { to: '/notifications' } : { type: 'button', 'aria-expanded': open }"
      :class="['header-round', 'bell-button', { 'has-unread': inbox.unread }]"
      :aria-label="label"
      :data-label="label"
      data-test="bell"
      @click="phone ? undefined : toggle()"
    >
      <AppIcon name="bell" />
      <!-- Téléphone (maquette Accueil) : la cloche seule et un point bleu ; le nombre est dans le nom accessible. -->
      <span
        v-if="inbox.unread && phone"
        class="bell-dot"
        aria-hidden="true"
        data-test="bell-dot"
      />
      <span
        v-else-if="inbox.unread"
        class="bell-count"
        aria-hidden="true"
        data-test="bell-badge"
      >{{ badge }}</span>
    </component>
    <div
      v-if="open && !phone"
      class="bell-panel"
      role="dialog"
      aria-label="Notifications"
      data-test="bell-panel"
    >
      <div class="bell-head">
        <strong>Notifications</strong>
        <button
          v-if="inbox.unread"
          type="button"
          class="link"
          data-test="read-all"
          @click="readAll"
        >
          Tout lire
        </button>
      </div>
      <p
        v-if="!inbox.items.length"
        class="hint bell-empty"
      >
        Aucune notification pour l'instant.
      </p>
      <ul
        v-else
        class="notifications-card"
      >
        <li
          v-for="item in recent"
          :key="item.id"
        >
          <NotificationRow
            :item="item"
            @open="select"
          />
        </li>
      </ul>
      <RouterLink
        to="/notifications"
        class="bell-all"
        data-test="bell-all"
        @click="open = false"
      >
        Tout voir
      </RouterLink>
    </div>
  </div>
</template>
