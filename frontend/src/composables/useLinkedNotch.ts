import { onBeforeUnmount, ref, watch, type Ref } from "vue";

// Liste reliée à une zone de détail (Candidatures sur ordinateur, maquette du 15 novembre, §11) : la flèche de la
// carte choisie (svg[data-arrow], 22 × 44) entre dans l'encoche du trait gauche de la zone (svg[data-notch], 24 × 43).
// L'encoche se place sur le centre de la flèche : top = centre − haut de la zone − 21,3 − 1,5 (le milieu de l'encoche
// dans son dessin, puis l'épaisseur du trait du haut). Si le centre sort de la partie visible de la liste (24 px de
// marge en haut et en bas, sous la barre fixe), la flèche et l'encoche se masquent et le trait redevient droit.
export const NOTCH_MIDDLE = 21.3;
export const LINE_WIDTH = 1.5;
export const VISIBLE_MARGIN = 24;

export function notchTop(arrowCenter: number, zoneTop: number): number {
  return Math.round((arrowCenter - zoneTop - NOTCH_MIDDLE - LINE_WIDTH) * 10) / 10;
}

export function arrowShown(center: number, visibleTop: number, visibleBottom: number): boolean {
  return center >= visibleTop + VISIBLE_MARGIN && center <= visibleBottom - VISIBLE_MARGIN;
}

// `list` : l'élément qui défile (la barre de recherche et de filtres y est collée en haut, [data-linked-tools]) ;
// `zone` : la zone de détail. Recalcul au défilement de la liste (écouteur passif), au changement de sélection et des
// cartes (MutationObserver), au redimensionnement de la fenêtre, de la liste, de la zone ou des cartes
// (ResizeObserver, barre d'outils comprise : elle pousse les cartes), une fois par image (requestAnimationFrame). Aucun minuteur.
export function useLinkedNotch(list: Ref<HTMLElement | null>, zone: Ref<HTMLElement | null>) {
  const top = ref(0);
  const visible = ref(false);
  let frame = 0;
  let resize: ResizeObserver | null = null;
  let mutation: MutationObserver | null = null;
  let bound: HTMLElement | null = null;

  function measure(): void {
    frame = 0;
    const l = list.value;
    const z = zone.value;
    if (!l || !z) {
      visible.value = false;
      return;
    }
    l.toggleAttribute("data-scrolled", l.scrollTop > 0);
    // La hauteur des colonnes part du haut de la grille (bandeau de démo, en-tête) jusqu'au bas de la fenêtre.
    const grid = l.parentElement;
    if (grid) grid.style.setProperty("--linked-top", `${Math.round(grid.getBoundingClientRect().top + window.scrollY)}px`);
    const arrow = l.querySelector<SVGElement>('[aria-current="true"] [data-arrow]');
    const box = arrow?.getBoundingClientRect();
    if (!box || !box.height) {
      visible.value = false;
      l.setAttribute("data-arrow-off", "");
      return;
    }
    const center = box.top + box.height / 2;
    const own = l.getBoundingClientRect();
    const tools = l.querySelector<HTMLElement>("[data-linked-tools]");
    const visibleTop = tools ? Math.max(own.top, tools.getBoundingClientRect().bottom) : own.top;
    const shown = arrowShown(center, visibleTop, own.bottom);
    visible.value = shown;
    l.toggleAttribute("data-arrow-off", !shown);
    top.value = notchTop(center, z.getBoundingClientRect().top);
  }

  function schedule(): void {
    if (!frame) frame = requestAnimationFrame(measure);
  }

  function observeCards(): void {
    if (!resize || !bound) return;
    resize.disconnect();
    resize.observe(bound);
    if (zone.value) resize.observe(zone.value);
    const tools = bound.querySelector("[data-linked-tools]");
    if (tools) resize.observe(tools);
    for (const card of bound.querySelectorAll(".list-card")) resize.observe(card);
  }

  function unbind(): void {
    bound?.removeEventListener("scroll", schedule);
    bound?.removeEventListener("transitionend", schedule);
    resize?.disconnect();
    mutation?.disconnect();
    bound = null;
  }

  function bind(): void {
    unbind();
    const l = list.value;
    if (!l || !zone.value) return;
    bound = l;
    l.addEventListener("scroll", schedule, { passive: true });
    // Les cartes entrent en glissant (TransitionGroup « card ») : position finale connue à la fin de la transition.
    l.addEventListener("transitionend", schedule, { passive: true });
    if (typeof ResizeObserver !== "undefined") resize = new ResizeObserver(schedule);
    if (typeof MutationObserver !== "undefined") {
      mutation = new MutationObserver(() => {
        observeCards();
        schedule();
      });
      mutation.observe(l, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-current"] });
    }
    observeCards();
    schedule();
    // Les polices chargées changent la hauteur des titres de rubrique, qui poussent les cartes sans les redimensionner.
    if (typeof document !== "undefined") void document.fonts?.ready.then(schedule);
  }

  watch([list, zone], bind, { flush: "post", immediate: true });
  if (typeof window !== "undefined") window.addEventListener("resize", schedule, { passive: true });
  onBeforeUnmount(() => {
    unbind();
    if (frame) cancelAnimationFrame(frame);
    if (typeof window !== "undefined") window.removeEventListener("resize", schedule);
  });

  return { top, visible, refresh: schedule };
}
