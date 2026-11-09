<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import type { InboxItem } from "../api/client";
import { timeInList } from "../dates";
import { plural } from "../format";
import { useDismissLayer } from "../composables/useDismissLayer";
import { useInbox } from "../composables/useInbox";
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import SidePanel from "./SidePanel.vue";

// Cloche des notifications (docs/15 §1 ; « Notifications » et non « Alertes », le nom de l'onglet des
// sources d'offres dans Candidatures), relue chaque minute. Sur téléphone, elle mène à la page
// /notifications (maquette Notifications). Sur ordinateur (maquette du 8 novembre, docs/143, D24), elle ouvre un
// panneau latéral non modal de 420 px : « Nouvelles » (non lues, point bleu) puis « Plus tôt », « Tout marquer
// comme lu » et, en pied, « Voir toutes les notifications ». Un seul panneau à la fois (useDismissLayer).
const REFRESH_MS = 60_000;
// Le panneau montre les plus récentes ; la page, toutes.
const PANEL_MAX = 8;

const { inbox, refresh, markRead, readAll } = useInbox();
const button = ref<HTMLElement | null>(null);
const layer = useDismissLayer("notifications");
const open = layer.open;
let timer: ReturnType<typeof setInterval> | undefined;
const { phone } = usePhone();
const recent = computed(() => inbox.value.items.slice(0, PANEL_MAX));
const fresh = computed(() => recent.value.filter((item) => !item.read_at));
const earlier = computed(() => recent.value.filter((item) => item.read_at));

const badge = computed(() => (inbox.value.unread > 9 ? "9+" : String(inbox.value.unread)));
const label = computed(() =>
  inbox.value.unread ? `Notifications, ${plural(inbox.value.unread, "nouvelle", "nouvelles")}` : "Notifications, aucune nouvelle",
);

// La ligne de détail : le message (sa première ligne) et l'heure, séparés par un point médian.
function detail(item: InboxItem): string {
  const text = item.message?.split("\n")[0] ?? "";
  return [text, timeInList(item.created_at)].filter(Boolean).join(" · ");
}

function select(item: InboxItem): void {
  layer.hide(false);
  void markRead(item);
}

function toggle(): void {
  const el = button.value instanceof HTMLElement ? button.value : null;
  layer.toggle(el);
  if (open.value) void refresh();
}

onMounted(() => {
  void refresh();
  timer = setInterval(() => void refresh(), REFRESH_MS);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div class="bell">
    <!-- Sans alerte : un rond neutre ; avec des alertes : une capsule orange clair, la cloche et le
         chiffre côte à côte (1.6.46). La légende reprend le nom accessible (WCAG 1.4.13). -->
    <component
      :is="phone ? 'RouterLink' : 'button'"
      ref="button"
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
    <SidePanel
      v-if="!phone"
      modeless
      :open="open"
      title="Notifications"
      close-label="Fermer les notifications"
      @close="layer.hide()"
    >
      <template #head-actions>
        <button
          v-if="inbox.unread"
          type="button"
          class="link side-panel-action"
          data-test="read-all"
          @click="readAll"
        >
          Tout marquer comme lu
        </button>
      </template>
      <div data-test="bell-panel">
        <p
          v-if="!inbox.items.length"
          class="hint bell-empty"
        >
          Aucune notification pour l'instant.
        </p>
        <template
          v-for="group in [{ title: 'Nouvelles', items: fresh }, { title: 'Plus tôt', items: earlier }]"
          :key="group.title"
        >
          <section
            v-if="group.items.length"
            class="bell-group"
          >
            <h3 class="panel-eyebrow">
              {{ group.title }}
            </h3>
            <ul class="bell-list">
              <li
                v-for="item in group.items"
                :key="item.id"
              >
                <component
                  :is="item.link ? 'RouterLink' : 'button'"
                  v-bind="item.link ? { to: item.link } : { type: 'button' }"
                  :class="['bell-row', { unread: !item.read_at }]"
                  data-test="notification"
                  @click="select(item)"
                >
                  <span
                    class="bell-row-dot"
                    :role="item.read_at ? undefined : 'img'"
                    :aria-label="item.read_at ? undefined : 'non lue'"
                    :data-test="item.read_at ? undefined : 'unread-dot'"
                  />
                  <span class="bell-row-body">
                    <span class="bell-row-title">{{ item.title }}</span>
                    <span class="bell-row-detail">{{ detail(item) }}</span>
                  </span>
                </component>
              </li>
            </ul>
          </section>
        </template>
      </div>
      <template #footer>
        <RouterLink
          to="/notifications"
          class="bell-all"
          data-test="bell-all"
          @click="layer.hide(false)"
        >
          Voir toutes les notifications
        </RouterLink>
      </template>
    </SidePanel>
  </div>
</template>
