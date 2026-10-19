// L'iconographie de jobA1 (docs/101) : grille de 24 px, trait de 1,8 px arrondi, coins doux,
// couleur du texte. Dessinées pour jobA1, aucun fichier repris. Le point pêche n'existe que sur
// « ai », l'icône des actions IA. Chaque entrée est le contenu du <svg> de AppIcon.
const circle = (cx: number, cy: number, r: number, extra = "") =>
  `<circle cx="${cx}" cy="${cy}" r="${r}"${extra}/>`;
const path = (d: string, extra = "") => `<path d="${d}"${extra}/>`;

export const ICONS = {
  // Repères et navigation
  search: circle(11, 11, 6.5) + path("M16 16l4.5 4.5"),
  calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/>' + path("M8 3v4M16 3v4M4 10h16"),
  inbox: path("M4 13l2.5-7h11L20 13v6H4z") + path("M4 13h4.5l1 2h5l1-2H20"),
  briefcase: '<rect x="3.5" y="7" width="17" height="12.5" rx="2.5"/>' + path("M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3.5 12.5h17"),
  "list-check": path("M4 6.5l1.5 1.5L8 5.5M4 12.5l1.5 1.5L8 11.5M4 18.5l1.5 1.5L8 17.5M11 7h9M11 13h9M11 19h9"),
  stats: path("M4.5 4v16h16") + path("M9 16v-4M12.5 16V8M16 16v-6"),
  book: path("M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z") + path("M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5"),
  news: '<rect x="3.5" y="5" width="17" height="14" rx="2"/>' + path("M7 9h6M7 12.5h10M7 16h10"),
  user: circle(12, 8, 4) + path("M4.5 20a7.5 7.5 0 0 1 15 0"),
  users: circle(9, 8.5, 3.5) + path("M3 19.5a6 6 0 0 1 12 0") + path("M15.5 5.2a3.5 3.5 0 0 1 0 6.6M17.5 14a6 6 0 0 1 3.5 5.5"),
  settings: path("M4 7h9M17 7h3M4 17h3M11 17h9") + circle(15, 7, 2) + circle(9, 17, 2),
  shield: path("M12 3.5l7 2.5v5.5c0 4.3-2.9 7.6-7 9-4.1-1.4-7-4.7-7-9V6z") + path("M9 12l2.2 2.2L15.5 10"),
  activity: path("M3.5 12h4l2.5-6.5 4 13 2.5-6.5h4"),
  logout: path("M10 4.5H6.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H10") + path("M14.5 8l4 4-4 4M18.5 12H9.5"),
  plug: path("M9 3.5v4M15 3.5v4M6.5 7.5h11v3a5.5 5.5 0 0 1-11 0z") + path("M12 16v4.5"),
  bell: path("M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15L6 16z") + path("M10 20a2 2 0 0 0 4 0"),
  filter: path("M4 5h16l-6.2 7.5v5.8l-3.6 1.7v-7.5z"),
  folder: path("M3.5 7a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"),
  mail: '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/>' + path("M4 7l8 6 8-6"),
  "clipboard-check": '<rect x="5" y="5" width="14" height="16" rx="2"/>' + path("M9 5V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1M9 13.5l2 2 4-4"),
  // Métadonnées
  pin: path("M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z") + circle(12, 9.5, 2.5),
  building: path("M5 20.5V5.5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v15") + path("M15 9.5h3a1 1 0 0 1 1 1v10M3.5 20.5h17M8.5 8.5h3M8.5 12h3M8.5 15.5h3"),
  home: path("M4 11l8-6.5 8 6.5") + path("M6 9.5V19.5h12V9.5M10 19.5v-5h4v5"),
  clock: circle(12, 12, 8.5) + path("M12 7.5V12l3 2"),
  globe: circle(12, 12, 9) + path("M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"),
  rate: circle(12, 12, 9) + path("M9 15l6-6M9.5 9.5h.01M14.5 14.5h.01"),
  tag: path("M3.5 12.2V4.5a1 1 0 0 1 1-1h7.7a1 1 0 0 1 .7.3l7.6 7.6a1 1 0 0 1 0 1.4l-7.7 7.7a1 1 0 0 1-1.4 0l-7.6-7.6a1 1 0 0 1-.3-.7z") + circle(8, 8, 1.3),
  eye: path("M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z") + circle(12, 12, 3),
  file: path("M7 3h7l4 4v14H7z") + path("M14 3v4h4M10 12h5M10 16h5"),
  // États
  check: circle(12, 12, 9, ' fill="currentColor" stroke="none"') + path("M8 12.5l2.5 2.5L16 9.5", ' stroke="var(--icon-on-fill, #fff)"'),
  done: path("M5 12.5l4.5 4.5L19 7.5"),
  "check-circle": circle(12, 12, 8.5) + path("M8.5 12.2l2.4 2.4 4.6-4.8"),
  alert: path("M12 4L2.8 19.5h18.4z") + path("M12 10v4M12 16.8h.01"),
  "x-circle": circle(12, 12, 8.5) + path("M9.2 9.2l5.6 5.6M14.8 9.2l-5.6 5.6"),
  star: path("M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"),
  trend: path("M7 17L17 7M9 7h8v8"),
  reply: path("M4 5h16v11H9l-5 4z") + path("M8 9.5h8M8 12.5h5"),
  message: path("M5 4.5h14a1.5 1.5 0 0 1 1.5 1.5v9.5a1.5 1.5 0 0 1-1.5 1.5H10l-4.5 3.5V17.5H5A1.5 1.5 0 0 1 3.5 16V6A1.5 1.5 0 0 1 5 4.5z"),
  play: path("M8 5.5v13l10.5-6.5z"),
  lock: '<rect x="5" y="10.5" width="14" height="10" rx="2"/>' + path("M8 10.5V8a4 4 0 0 1 8 0v2.5"),
  // Actions
  send: path("M20 4L3.5 11l6.5 2.5L12.5 20z") + path("M20 4l-10 9.5"),
  refresh: path("M19 12a7 7 0 1 1-2.1-5") + path("M19 4.5V9h-4.5"),
  download: path("M12 4v11M7.5 10.5L12 15l4.5-4.5M5 19.5h14"),
  upload: path("M12 15.5V4.5M7.5 9L12 4.5 16.5 9M5 19.5h14"),
  copy: '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/>' + path("M15.5 8.5V6.5a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"),
  trash: path("M4.5 7h15M10 4h4M6.5 7l.8 12a1.5 1.5 0 0 0 1.5 1.5h6.4a1.5 1.5 0 0 0 1.5-1.5l.8-12M10 11v5.5M14 11v5.5"),
  pencil: path("M15 5l4 4L8.5 19.5H4.5v-4z") + path("M13 7l4 4"),
  plus: path("M12 5v14M5 12h14"),
  close: path("M6 6l12 12M18 6L6 18"),
  "arrow-left": path("M19 12H5M11 6l-6 6 6 6"),
  "arrow-right": path("M5 12h14M13 6l6 6-6 6"),
  "arrow-up": path("M12 19V5M6 11l6-6 6 6"),
  "arrow-down": path("M12 5v14M6 13l6 6 6-6"),
  chevron: path("M9 6l6 6-6 6"),
  "chevron-down": path("M6 9l6 6 6-6"),
  external: path("M14 4.5h5.5V10M19.5 4.5L11 13") + path("M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"),
  bookmark: path("M6.5 4.5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16l-5.5-4-5.5 4z"),
  more: circle(5.5, 12, 0.9, ' fill="currentColor"') + circle(12, 12, 0.9, ' fill="currentColor"') + circle(18.5, 12, 0.9, ' fill="currentColor"'),
  // L'étincelle à 4 branches, réservée à l'IA (docs/99) : la rubrique IA des Réglages.
  spark: path("M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8z") + path("M18.5 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"),
  // « Action IA » (docs/101) : un carré aux coins doux, ouvert en haut à droite, et le point pêche.
  ai: path("M13 4.5H7A2.5 2.5 0 0 0 4.5 7v10A2.5 2.5 0 0 0 7 19.5h10a2.5 2.5 0 0 0 2.5-2.5v-6") + circle(18.5, 5.5, 2.6, ' class="icon-ai-dot" stroke="none"'),
} as const;

export type IconName = keyof typeof ICONS;
