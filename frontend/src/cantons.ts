// Cantons suisses en toutes lettres (docs/43 n° 24) : « VD » s'affiche « Vaud ».
const CANTONS: Record<string, string> = {
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

const plain = (text: string): string =>
  text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[-'’.]/g, " ").replace(/\s+/g, " ").trim();
const CANTON_BY_NAME = new Map(Object.entries(CANTONS).map(([code, name]) => [plain(name), code]));
// Le canton des villes les plus fréquentes (backend/src/jobbot/core/places.py, CITY_CANTON), avec leurs noms français.
const CITY_CANTON: Record<string, string> = {
  bern: "BE", berne: "BE", biel: "BE", bienne: "BE", thun: "BE", thoune: "BE", zurich: "ZH", winterthur: "ZH",
  geneve: "GE", basel: "BS", bale: "BS", lausanne: "VD", montreux: "VD", "yverdon les bains": "VD", yverdon: "VD",
  renens: "VD", morges: "VD", nyon: "VD", vevey: "VD", luzern: "LU", lucerne: "LU", fribourg: "FR", neuchatel: "NE",
  "la chaux de fonds": "NE", solothurn: "SO", soleure: "SO", schaffhausen: "SH", schaffhouse: "SH", "st gallen": "SG",
  "saint gall": "SG", zug: "ZG", zoug: "ZG", chur: "GR", coire: "GR", sion: "VS", sierre: "VS", murten: "FR",
  morat: "FR", delemont: "JU", bellinzona: "TI", bellinzone: "TI", lugano: "TI", aarau: "AG", baden: "AG",
};

/** Le code du canton quand le lieu est un canton (« VD », « Vaud »), sinon `null`. */
export function cantonCode(place: string): string | null {
  const code = place.trim().toUpperCase();
  return CANTONS[code] ? code : (CANTON_BY_NAME.get(plain(place)) ?? null);
}

/** Le canton d'une ville : nommé (« Lausanne, VD ») ou celui d'une ville connue (« Lausanne » → VD). */
export function cantonOfCity(place: string): string | null {
  const named = place.match(/(?<![A-Za-z])([A-Z]{2})(?![A-Za-z])/g)?.find((code) => CANTONS[code]);
  return named ?? CITY_CANTON[plain(place.split(",")[0] ?? "")] ?? null;
}
