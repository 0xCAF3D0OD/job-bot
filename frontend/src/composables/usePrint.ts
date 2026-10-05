// Impression d'un document (lettre, CV, preuves ORP) en PDF par le navigateur.
//
// - seule la feuille est imprimée : une copie est placée dans #print-root, le reste de la page
//   est retiré de la mise en page (sinon des pages blanches s'ajoutent) ;
// - marges de page à 0 : le navigateur n'a plus de place pour ses en-têtes et pieds de page
//   (titre, adresse, date, numéro de page) ; la marge est recréée à l'intérieur ;
// - si le document dépasse à peine d'une page, il est légèrement réduit pour tenir sur une
//   page de moins, au lieu de laisser une dernière page presque vide.

const MM = 96 / 25.4;
const MARGIN_MM = 14;
// Débordement toléré avant de réduire : au-delà, la page suivante est assez remplie.
const SHRINK_UP_TO = 0.35;
const MIN_ZOOM = 0.8;

export interface PrintOptions {
  // Titre du document : nom de fichier proposé par « Enregistrer au format PDF ».
  title: string;
  landscape?: boolean;
}

export function zoomToFit(contentHeight: number, pageHeight: number): number {
  const pages = contentHeight / pageHeight;
  const whole = Math.floor(pages);
  if (pages <= 1 || pages - whole > SHRINK_UP_TO || whole === pages) return 1;
  return Math.max(MIN_ZOOM, (whole / pages) * 0.97);
}

export function printSheet(sheet: HTMLElement, options: PrintOptions): void {
  document.getElementById("print-root")?.remove();
  const root = document.createElement("div");
  root.id = "print-root";
  if (options.landscape) root.classList.add("landscape");
  const copy = sheet.cloneNode(true) as HTMLElement;
  copy.classList.remove("busy");
  root.appendChild(copy);
  document.body.appendChild(root);

  // Mesure hors écran, à la largeur imprimée.
  const [width, height] = options.landscape ? [297, 210] : [210, 297];
  root.classList.add("measuring");
  root.style.width = `${width * MM}px`;
  const zoom = zoomToFit(root.scrollHeight - 2 * MARGIN_MM * MM, (height - 2 * MARGIN_MM) * MM);
  root.classList.remove("measuring");
  root.style.width = "";
  if (zoom < 1) copy.style.setProperty("zoom", String(zoom));

  const previousTitle = document.title;
  document.title = options.title;
  document.body.classList.add("printing");
  const cleanUp = () => {
    document.body.classList.remove("printing");
    document.title = previousTitle;
    root.remove();
    window.removeEventListener("afterprint", cleanUp);
  };
  window.addEventListener("afterprint", cleanUp);
  window.print();
}
