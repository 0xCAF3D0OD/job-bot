import { computed, ref } from "vue";

import { api, type Inbox, type InboxItem } from "../api/client";
import { plural } from "../format";
import { offerUndo } from "./useUndo";

// Les notifications (maquette Notifications, docs/139 étape 9) : une seule liste, partagée par la cloche et
// la page /notifications, relue par la cloche chaque minute.
const inbox = ref<Inbox>({ unread: 0, items: [] });
// « Tout lire » attend 6 s avant de partir au serveur (useUndo, docs/108) : une relecture faite entre-temps
// garde ces notifications lues à l'écran.
let reading: Set<number> | null = null;

function apply(data: Inbox): void {
  if (!reading) {
    inbox.value = data;
    return;
  }
  const at = new Date().toISOString();
  const items = data.items.map((item) => (reading!.has(item.id) && !item.read_at ? { ...item, read_at: at } : item));
  inbox.value = { unread: items.filter((item) => !item.read_at).length, items };
}

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/inbox");
    if (data) apply(data);
  } catch {
    // API momentanément injoignable : on réessaiera à la prochaine relecture.
  }
}

// Toucher une ligne la marque comme lue, tout de suite à l'écran ; le serveur renvoie la liste à jour.
async function markRead(item: InboxItem): Promise<void> {
  if (item.read_at) return;
  const at = new Date().toISOString();
  const items = inbox.value.items.map((i) => (i.id === item.id ? { ...i, read_at: at } : i));
  inbox.value = { unread: items.filter((i) => !i.read_at).length, items };
  try {
    const { data } = await api.POST("/api/inbox/{notification_id}/read", {
      params: { path: { notification_id: item.id } },
    });
    if (data) apply(data);
  } catch {
    // La prochaine relecture remettra l'état du serveur.
  }
}

// « Tout lire » : lu tout de suite, envoyé au serveur après 6 s sauf « Annuler » (décision du 2026-11-04).
function readAll(): void {
  const ids = new Set(inbox.value.items.filter((item) => !item.read_at).map((item) => item.id));
  if (!ids.size) return;
  const before = inbox.value;
  reading = ids;
  apply(before);
  void offerUndo({
    message: `${plural(ids.size, "notification marquée comme lue", "notifications marquées comme lues")}`,
    commit: async (keepalive) => {
      const { data } = await api.POST("/api/inbox/read-all", { keepalive });
      reading = null;
      if (!data) return false;
      apply(data);
    },
    restore: () => {
      reading = null;
      // Ce qui est arrivé entre-temps reste ; seules les notifications lues par « Tout lire » redeviennent non lues.
      const items = inbox.value.items.map((item) => (ids.has(item.id) ? { ...item, read_at: null } : item));
      inbox.value = { unread: items.filter((item) => !item.read_at).length, items };
    },
  });
}

export function useInbox() {
  const unread = computed(() => inbox.value.unread);
  return { inbox, unread, refresh, markRead, readAll };
}
