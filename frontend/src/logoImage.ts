// Un logo servi mais vide (docs/14 §4) : une image minuscule, ou presque toute transparente ou blanche.
// Le serveur refuse déjà les images génériques (jobbot logos --clean-generic) ; ce contrôle couvre celles
// enregistrées avant, pour que l'interface montre les initiales au lieu d'un carré vide.
const SIDE = 16;

export function isBlankLogo(img: HTMLImageElement): boolean {
  if (img.naturalWidth <= 2 || img.naturalHeight <= 2) return true;
  try {
    const canvas = document.createElement("canvas");
    canvas.width = SIDE;
    canvas.height = SIDE;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return false;
    context.drawImage(img, 0, 0, SIDE, SIDE);
    const { data } = context.getImageData(0, 0, SIDE, SIDE);
    let ink = 0;
    for (let i = 0; i < data.length; i += 4) {
      const alpha = data[i + 3]!;
      const light = Math.min(data[i]!, data[i + 1]!, data[i + 2]!);
      // Un point visible et pas blanc : de l'encre.
      if (alpha > 24 && light < 235) ink += 1;
    }
    return ink < 3;
  } catch {
    // Lecture refusée (image d'une autre origine) : on garde l'image.
    return false;
  }
}
