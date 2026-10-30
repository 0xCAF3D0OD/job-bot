import { onMounted, onUnmounted } from "vue";

// Fichiers préparés par la plateforme (docs/59 §4) : PDF, Word, export ORP, agenda. Les liens
// `<a download href="/api/…">` restent tels quels ; un seul écouteur les télécharge lui-même pour
// que le retour soit sur le lien, qui garde sa largeur : pendant la préparation, son icône devient
// un indicateur ; prêt, une coche 2 secondes ; en échec, « Réessayer » (feuille de style,
// `a[download][data-file]`). L'état et la taille sont annoncés (aria-live), puisqu'ils ne s'écrivent plus.
const DONE_MS = 2000;
const FAILED_MS = 4000;

export function fileName(disposition: string | null, href: string): string {
  const star = disposition?.match(/filename\*=UTF-8''([^;]+)/i);
  if (star?.[1]) return decodeURIComponent(star[1]);
  const plain = disposition?.match(/filename="?([^";]+)"?/i);
  if (plain?.[1]) return plain[1];
  return new URL(href, window.location.origin).pathname.split("/").pop() || "fichier";
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`;
}

function save(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

let live: HTMLElement | null = null;
function announce(text: string): void {
  if (!live || !live.isConnected) {
    live = document.createElement("span");
    live.className = "visually-hidden";
    live.setAttribute("role", "status");
    live.dataset.test = "file-status";
    document.body.append(live);
  }
  live.textContent = text;
}

function linkLabel(link: HTMLAnchorElement): string {
  return (link.textContent ?? "").replace(/\s+/g, " ").trim() || "Fichier";
}

const SAYS = {
  preparing: (name: string) => `${name} : préparation…`,
  done: (name: string, size: string) => `${name} téléchargé${size ? `, ${size}` : ""}.`,
  failed: (name: string) => `${name} : échec, réessaie.`,
};

function mark(link: HTMLAnchorElement, state: "preparing" | "done" | "failed" | null, size = ""): void {
  if (state) link.dataset.file = state;
  else delete link.dataset.file;
  link.dataset.size = size;
  if (state) announce(SAYS[state](linkLabel(link), size));
}

export async function download(link: HTMLAnchorElement): Promise<void> {
  const href = link.getAttribute("href") ?? "";
  mark(link, "preparing");
  try {
    const response = await fetch(href, { credentials: "same-origin" });
    if (!response.ok) throw new Error(String(response.status));
    const blob = await response.blob();
    save(blob, fileName(response.headers.get("content-disposition"), href));
    mark(link, "done", fileSize(blob.size));
    setTimeout(() => link.dataset.file === "done" && mark(link, null), DONE_MS);
  } catch {
    mark(link, "failed");
    setTimeout(() => link.dataset.file === "failed" && mark(link, null), FAILED_MS);
  }
}

export function useFileDownloads(): void {
  function onClick(event: MouseEvent): void {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = (event.target as Element | null)?.closest?.("a[download]");
    if (!(link instanceof HTMLAnchorElement)) return;
    if (!(link.getAttribute("href") ?? "").startsWith("/api/") || link.dataset.file === "preparing") return;
    event.preventDefault();
    void download(link);
  }
  onMounted(() => document.addEventListener("click", onClick));
  onUnmounted(() => document.removeEventListener("click", onClick));
}
