import { onBeforeUnmount, ref, watch, type Ref } from "vue";

// Liste reliée à une zone de détail (Candidatures sur ordinateur, §18 du 15 novembre) : la flèche de la carte choisie
// (svg[data-arrow], 22 × 60) touche la pointe du rail (svg[data-notch], le même tracé en miroir). La pointe se place
// sur le centre de la flèche : top = centre − haut de la zone − 30 (la moitié du dessin).
// Quand la carte choisie sort de la partie visible de la liste, une carte compacte (LinkedPin, 76 px) se fixe à 12 px
// sous la barre de filtres (sortie par le haut) ou à 12 px du bas (sortie par le bas) : elle porte la flèche, et la
// pointe se place en face d'elle. La flèche et la pointe ne sont donc jamais masquées.
export const NOTCH_HALF = 30;
export const PIN_GAP = 12;
export const PIN_HEIGHT = 76;

export type PinSide = "top" | "bottom" | null;

export function notchTop(arrowCenter: number, zoneTop: number): number {
  return Math.round((arrowCenter - zoneTop - NOTCH_HALF) * 10) / 10;
}

// La carte choisie s'épingle dès que son centre passe la ligne où se trouverait le centre de la carte compacte : la
// flèche passe de l'une à l'autre sans saut.
export function pinSide(center: number, visibleTop: number, visibleBottom: number): PinSide {
  const half = PIN_GAP + PIN_HEIGHT / 2;
  if (center < visibleTop + half) return "top";
  if (center > visibleBottom - half) return "bottom";
  return null;
}

// Le centre de la flèche de la carte compacte, d'après sa place fixe (elle n'est pas encore dessinée à ce moment-là).
export function pinCenter(side: Exclude<PinSide, null>, visibleTop: number, visibleBottom: number): number {
  const half = PIN_GAP + PIN_HEIGHT / 2;
  return side === "top" ? visibleTop + half : visibleBottom - half;
}

// `list` : la colonne de liste. La barre de recherche et de filtres ([data-linked-tools]) y reste en haut, hors de ce
// qui défile ; seules les cartes défilent, dans `.linked-cards` (la barre de défilement commence donc sous les filtres) ;
// `zone` : la zone de détail. Recalcul au défilement de la liste (écouteur passif), au changement de sélection et des
// cartes (MutationObserver), au redimensionnement de la fenêtre, de la liste, de la zone ou des cartes
// (ResizeObserver, barre d'outils comprise : elle pousse les cartes), une fois par image (requestAnimationFrame). Aucun minuteur.
// Sur la liste : data-scrolled (ombre sous la barre), data-pinned="top|bottom" (la carte compacte montrée) et
// --linked-pin-top (sa place sous la barre).
export function useLinkedNotch(list: Ref<HTMLElement | null>, zone: Ref<HTMLElement | null>) {
  const top = ref(0);
  const visible = ref(false);
  let frame = 0;
  let resize: ResizeObserver | null = null;
  let mutation: MutationObserver | null = null;
  let bound: HTMLElement | null = null;
  let scroller: HTMLElement | null = null;

  // Ce qui défile dans la colonne : `.linked-cards`, ou la colonne elle-même à défaut.
  function cardsOf(l: HTMLElement): HTMLElement {
    return l.querySelector<HTMLElement>(":scope > .linked-cards") ?? l;
  }

  function setPinned(l: HTMLElement, side: PinSide): void {
    if (side) l.setAttribute("data-pinned", side);
    else l.removeAttribute("data-pinned");
  }

  function measure(): void {
    frame = 0;
    const l = list.value;
    const z = zone.value;
    if (!l || !z) {
      visible.value = false;
      return;
    }
    const s = cardsOf(l);
    l.toggleAttribute("data-scrolled", s.scrollTop > 0);
    // La hauteur des colonnes part du haut de la grille (bandeau de démo, en-tête) jusqu'au bas de la fenêtre.
    const grid = l.parentElement;
    if (grid) grid.style.setProperty("--linked-top", `${Math.round(grid.getBoundingClientRect().top + window.scrollY)}px`);
    const own = s.getBoundingClientRect();
    const tools = l.querySelector<HTMLElement>("[data-linked-tools]");
    // Le bas de ce que montre la barre (le champ de filtre, les filtres actifs), sans ses marges : la carte compacte
    // se place 12 px dessous, jamais collée.
    const shown = tools ? [...tools.children].map((c) => c.getBoundingClientRect()).filter((r) => r.height) : [];
    const visibleTop = shown.length ? Math.max(...shown.map((r) => r.bottom)) : own.top;
    l.style.setProperty("--linked-pin-top", `${Math.round(visibleTop - l.getBoundingClientRect().top + PIN_GAP)}px`);
    const arrow = l.querySelector<SVGElement>('[aria-current="true"] > [data-arrow]');
    // Le trait réel de la carte choisie (1,5 px déclaré, arrondi par certains navigateurs) : la flèche s'y accroche.
    const card = arrow?.parentElement;
    if (card) card.style.setProperty("--linked-card-border", getComputedStyle(card).borderRightWidth);
    const box = arrow?.getBoundingClientRect();
    if (!box || !box.height) {
      visible.value = false;
      setPinned(l, null);
      return;
    }
    const center = box.top + box.height / 2;
    const side = pinSide(center, visibleTop, own.bottom);
    setPinned(l, side);
    visible.value = true;
    // La carte compacte vient d'apparaître : sa flèche est mesurée tout de suite (le navigateur la place avant de
    // répondre), sinon sa place prévue.
    const pinned = side ? l.querySelector<SVGElement>(`.linked-pin[data-side="${side}"] [data-arrow]`)?.getBoundingClientRect() : null;
    const target = side ? (pinned?.height ? pinned.top + pinned.height / 2 : pinCenter(side, visibleTop, own.bottom)) : center;
    top.value = notchTop(target, z.getBoundingClientRect().top);
  }

  function schedule(): void {
    if (!frame) frame = requestAnimationFrame(measure);
  }

  function observeCards(): void {
    if (!resize || !bound) return;
    resize.disconnect();
    resize.observe(bound);
    if (scroller && scroller !== bound) resize.observe(scroller);
    if (zone.value) resize.observe(zone.value);
    const tools = bound.querySelector("[data-linked-tools]");
    if (tools) resize.observe(tools);
    for (const card of bound.querySelectorAll(".list-card")) resize.observe(card);
  }

  function unbind(): void {
    scroller?.removeEventListener("scroll", schedule);
    bound?.removeEventListener("transitionend", schedule);
    resize?.disconnect();
    mutation?.disconnect();
    if (bound) setPinned(bound, null);
    bound = null;
    scroller = null;
  }

  function bind(): void {
    unbind();
    const l = list.value;
    if (!l || !zone.value) return;
    bound = l;
    scroller = cardsOf(l);
    scroller.addEventListener("scroll", schedule, { passive: true });
    // Les cartes entrent en glissant (TransitionGroup « card ») : position finale connue à la fin de la transition.
    l.addEventListener("transitionend", schedule, { passive: true });
    if (typeof ResizeObserver !== "undefined") resize = new ResizeObserver(schedule);
    if (typeof MutationObserver !== "undefined") {
      // Au changement de sélection, mesure tout de suite (le rappel passe avant le dessin) : la flèche et la pointe du
      // rail apparaissent dans la même image, sans saut d'une image à l'autre.
      mutation = new MutationObserver(() => {
        observeCards();
        if (frame) cancelAnimationFrame(frame);
        measure();
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
