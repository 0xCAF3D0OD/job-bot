// Cantons suisses en toutes lettres (docs/43 n° 24) : « VD » s'affiche « Vaud ».
export const CANTONS: Record<string, string> = {
  AG: "Argovie",
  AI: "Appenzell Rhodes-Intérieures",
  AR: "Appenzell Rhodes-Extérieures",
  BE: "Berne",
  BL: "Bâle-Campagne",
  BS: "Bâle-Ville",
  FR: "Fribourg",
  GE: "Genève",
  GL: "Glaris",
  GR: "Grisons",
  JU: "Jura",
  LU: "Lucerne",
  NE: "Neuchâtel",
  NW: "Nidwald",
  OW: "Obwald",
  SG: "Saint-Gall",
  SH: "Schaffhouse",
  SO: "Soleure",
  SZ: "Schwytz",
  TG: "Thurgovie",
  TI: "Tessin",
  UR: "Uri",
  VD: "Vaud",
  VS: "Valais",
  ZG: "Zoug",
  ZH: "Zurich",
};

export function placeLabel(value: string): string {
  return CANTONS[value.trim().toUpperCase()] ?? value;
}
