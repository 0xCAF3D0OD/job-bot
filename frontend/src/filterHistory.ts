import { getCurrentInstance, onBeforeUnmount, onMounted, watch } from "vue";
import type { Router } from "vue-router";

// L’entrée d’historique d’une feuille ou d’un panneau de filtres (Kevin, 17.11,
// docs/decisions/2026-11-17-1327-filtres-historique.md) :
// 1. une seule entrée par application, avec les filtres dans l’adresse : les choix faits pendant l’ouverture remplacent
//    l’adresse de l’entrée ajoutée à l’ouverture ; à la fermeture, elle reste si l’adresse a changé, sinon on revient
//    en arrière. Retour, une fois fermé, ramène alors les filtres d’avant ;
// 2. toute fermeture applique, le bouton retour compris (13 h 43) : retour pendant l’ouverture fait revenir le
//    navigateur à l’entrée d’avant ; si l’adresse avait changé, l’entrée choisie est remise AVANT que le routeur ne lise
//    l’adresse (écouteur posé avant le sien), pour que la liste ne montre jamais les filtres d’avant (14 h 07) ;
// 3. le tri d’Envoyées est une préférence du compte, hors de l’historique (14 h 07) : « tri » y est neutre
//    (`NEUTRAL`) ; un changement de tri seul ne crée pas d’entrée, et la page remet son tri dans l’adresse.
// `sheet` marque l’entrée, `sheetHref` garde l’adresse à l’ouverture (reprise telle quelle d’une feuille à l’autre).

/** Paramètres d’adresse hors de l’historique, par page : le tri d’Envoyées, préférence du compte (Kevin, 17.11). */
const NEUTRAL: Record<string, string[]> = { "/candidatures/suivi": ["tri"] };

/** Deux adresses qui ne diffèrent que par des paramètres neutres comptent comme la même application. */
function sameApplication(a: string, b: string): boolean {
  if (a === b) return true;
  try {
    const [x, y] = [new URL(a), new URL(b)];
    if (x.pathname !== y.pathname) return false;
    for (const name of NEUTRAL[x.pathname] ?? []) {
      x.searchParams.delete(name);
      y.searchParams.delete(name);
    }
    x.searchParams.sort();
    y.searchParams.sort();
    return x.href === y.href;
  } catch {
    return false;
  }
}

function withoutMark(state: Record<string, unknown> | null): Record<string, unknown> {
  const rest = { ...(state ?? {}) };
  delete rest.sheet;
  delete rest.sheetHref;
  return rest;
}

// Les écouteurs du bouton retour passent AVANT celui du routeur : main.ts importe ce module en premier, avant que
// createWebHistory() (router.ts) ne pose le sien ; Chrome appelle les écouteurs de window dans l’ordre d’inscription.
const backListeners = new Set<() => void>();
if (typeof window !== "undefined") window.addEventListener("popstate", () => [...backListeners].forEach((listener) => listener()));
export function onBack(listener: () => void): void {
  backListeners.add(listener);
}
export function offBack(listener: () => void): void {
  backListeners.delete(listener);
}

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
  if (sameApplication(String(state.sheetHref), window.location.href)) {
    window.history.back();
    return;
  }
  window.history.replaceState(withoutMark(state), "", window.location.href);
}

let serial = 0;

/** Suit l’adresse pendant l’ouverture, pour que le bouton retour applique les choix (règle 2). */
export function useEntryTracker(): { start: () => void; stop: () => void; reapply: () => void } {
  // Le routeur de l’application, s’il y en a un (sans import de vue-router : des tests le remplacent).
  const router = (getCurrentInstance()?.appContext.config.globalProperties.$router as Router | undefined) ?? null;
  let active = false;
  let opened = "";
  let last = "";
  let lastState: Record<string, unknown> | null = null;
  function sample(): void {
    // Seulement sur l’entrée de la feuille (après un retour, l’adresse est déjà celle d’avant).
    const state = window.history.state as Record<string, unknown> | null;
    if (!active || !state?.sheet) return;
    last = window.location.href;
    lastState = state;
  }
  watch(() => router?.currentRoute.value.fullPath, sample);
  return {
    start() {
      active = true;
      opened = String((window.history.state as Record<string, unknown> | null)?.sheetHref ?? window.location.href);
      sample();
    },
    stop() {
      active = false;
    },
    // Sur popstate, avant le routeur : le navigateur est revenu à l’entrée d’avant, le routeur pas encore. On remet
    // l’entrée choisie par-dessus ; le routeur lit alors l’adresse choisie et la liste ne bouge pas.
    reapply() {
      sample();
      active = false;
      if (!last || sameApplication(last, opened)) return;
      window.history.pushState(withoutMark(lastState), "", last);
    },
  };
}

/** Pour un panneau monté pendant son ouverture (« Plus de filtres » sur ordinateur, v-if) : l’entrée à l’arrivée,
 *  la fermeture qui applique au départ ; retour pendant l’ouverture applique aussi et appelle `onBack`. */
export function useFilterEntry(close: () => void): void {
  const key = `panel-${(serial += 1)}`;
  const tracker = useEntryTracker();
  let mine = false;
  function onPopState(): void {
    if (!mine) return;
    mine = false;
    offBack(onPopState);
    tracker.reapply();
    close();
  }
  onMounted(() => {
    mine = enterEntry(key, false);
    if (mine) {
      tracker.start();
      onBack(onPopState);
    }
  });
  onBeforeUnmount(() => {
    tracker.stop();
    offBack(onPopState);
    if (!mine) return;
    mine = false;
    leaveEntry(key);
  });
}
