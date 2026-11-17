import { getCurrentInstance, onBeforeUnmount, onMounted, watch } from "vue";
import type { Router } from "vue-router";

// L’entrée d’historique d’une feuille ou d’un panneau de filtres (Kevin, 17.11,
// docs/decisions/2026-11-17-1327-filtres-historique.md) :
// 1. une seule entrée par application, avec les filtres dans l’adresse : les choix faits pendant l’ouverture remplacent
//    l’adresse de l’entrée ajoutée à l’ouverture ; à la fermeture, elle reste si l’adresse a changé, sinon on revient
//    en arrière. Retour, une fois fermé, ramène alors les filtres d’avant ;
// 2. toute fermeture applique, le bouton retour compris (Kevin, 17.11, 13 h 43, remplace la règle de 13 h 27) : retour
//    pendant l’ouverture fait revenir le navigateur à l’entrée d’avant ; si l’adresse avait changé, on la remet par une
//    nouvelle entrée (la même application), sinon on ferme seulement.
// `sheet` marque l’entrée, `sheetHref` garde l’adresse à l’ouverture (reprise telle quelle d’une feuille à l’autre).

/** Ajoute (ou reprend, `inherited`) l’entrée de `key`. Rend false si l’historique n’est pas disponible. */
export function enterEntry(key: string, inherited: boolean): boolean {
  if (typeof window === "undefined" || !window.history?.pushState) return false;
  const current = (window.history.state ?? {}) as Record<string, unknown>;
  const href = window.location.href;
  // Reprise de la feuille précédente : son entrée devient la nôtre (pas de retour en arrière entre deux).
  if (inherited && current.sheet) window.history.replaceState({ ...current, sheet: key, sheetHref: current.sheetHref ?? href }, "", href);
  else window.history.pushState({ ...current, sheet: key, sheetHref: href }, "", href);
  return true;
}

/** Fermeture qui applique : l’entrée de `key` reste si l’adresse a changé (sans sa marque), sinon retour arrière. */
export function leaveEntry(key: string): void {
  const state = window.history.state as Record<string, unknown> | null;
  if (state?.sheet !== key) return;
  if (state.sheetHref === window.location.href) {
    window.history.back();
    return;
  }
  const rest = { ...state };
  delete rest.sheet;
  delete rest.sheetHref;
  window.history.replaceState(rest, "", window.location.href);
}

let serial = 0;

/** Suit l’adresse pendant l’ouverture, pour que le bouton retour applique les choix (règle 2). */
export function useEntryTracker(): { start: () => void; stop: () => void; reapply: () => void } {
  // Le routeur de l’application, s’il y en a un (sans import de vue-router : des tests le remplacent).
  const router = (getCurrentInstance()?.appContext.config.globalProperties.$router as Router | undefined) ?? null;
  let active = false;
  let opened = "";
  let last = "";
  watch(
    () => router?.currentRoute.value.fullPath,
    () => {
      // Seulement sur l’entrée de la feuille : le navigateur peut avoir fini le retour avant l’événement popstate.
      if (active && (window.history.state as Record<string, unknown> | null)?.sheet) last = window.location.href;
    },
  );
  return {
    start() {
      active = true;
      last = window.location.href;
      opened = String((window.history.state as Record<string, unknown> | null)?.sheetHref ?? last);
    },
    stop() {
      active = false;
    },
    // Appelé sur l’événement popstate : le navigateur est déjà revenu à l’entrée d’avant.
    reapply() {
      active = false;
      if (!router || last === opened || !last.startsWith(window.location.origin)) return;
      // `force` : la navigation du retour (vers l’adresse d’avant) est encore en cours et sera annulée ; le routeur
      // croit toujours être à l’adresse choisie et refuserait sinon un doublon, sans ajouter l’entrée.
      const { path, query, hash } = router.resolve(last.slice(window.location.origin.length));
      void router.push({ path, query, hash, force: true });
    },
  };
}

/** Pour un panneau monté pendant son ouverture (« Plus de filtres » sur ordinateur, v-if) : l’entrée à l’arrivée,
 *  la fermeture qui applique au départ ; retour pendant l’ouverture applique aussi et appelle `onBack`. */
export function useFilterEntry(onBack: () => void): void {
  const key = `panel-${(serial += 1)}`;
  const tracker = useEntryTracker();
  let mine = false;
  function onPopState(): void {
    if (!mine) return;
    mine = false;
    window.removeEventListener("popstate", onPopState);
    tracker.reapply();
    onBack();
  }
  onMounted(() => {
    mine = enterEntry(key, false);
    if (mine) {
      tracker.start();
      window.addEventListener("popstate", onPopState);
    }
  });
  onBeforeUnmount(() => {
    tracker.stop();
    window.removeEventListener("popstate", onPopState);
    if (!mine) return;
    mine = false;
    leaveEntry(key);
  });
}
