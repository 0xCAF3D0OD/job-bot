import { onMounted, onUnmounted, ref } from "vue";

import { ILLUSTRATE_AFTER_MS, ILLUSTRATION_MIN_MS } from "./useLoadingGate";

// Fichiers préparés par la plateforme (docs/58 §3.2) : PDF, Word, export ORP, agenda. Les liens
// `<a download href="/api/…">` restent tels quels ; un seul écouteur les télécharge lui-même pour
// savoir quand le fichier est prêt. S'il tarde plus de 0,4 s, l'illustration « processing »
// s'affiche (au moins 0,6 s), puis le fichier est enregistré comme avant.
export type FileState = "idle" | "preparing" | "failed";

export function fileName(disposition: string | null, href: string): string {
  const star = disposition?.match(/filename\*=UTF-8''([^;]+)/i);
  if (star?.[1]) return decodeURIComponent(star[1]);
  const plain = disposition?.match(/filename="?([^";]+)"?/i);
  if (plain?.[1]) return plain[1];
  return new URL(href, window.location.origin).pathname.split("/").pop() || "fichier";
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

export function useFileDownloads() {
  const state = ref<FileState>("idle");
  let busy = false;

  async function download(href: string): Promise<void> {
    busy = true;
    let shownAt = 0;
    const timer = setTimeout(() => {
      state.value = "preparing";
      shownAt = Date.now();
    }, ILLUSTRATE_AFTER_MS);
    try {
      const response = await fetch(href, { credentials: "same-origin" });
      if (!response.ok) throw new Error(String(response.status));
      const blob = await response.blob();
      clearTimeout(timer);
      if (shownAt) await new Promise((r) => setTimeout(r, Math.max(0, ILLUSTRATION_MIN_MS - (Date.now() - shownAt))));
      save(blob, fileName(response.headers.get("content-disposition"), href));
      state.value = "idle";
    } catch {
      clearTimeout(timer);
      state.value = "failed";
      setTimeout(() => (state.value = "idle"), 4000);
    } finally {
      busy = false;
    }
  }

  function onClick(event: MouseEvent): void {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = (event.target as Element | null)?.closest?.("a[download]");
    if (!(link instanceof HTMLAnchorElement)) return;
    const href = link.getAttribute("href") ?? "";
    if (!href.startsWith("/api/") || busy) return;
    event.preventDefault();
    void download(href);
  }

  onMounted(() => document.addEventListener("click", onClick));
  onUnmounted(() => document.removeEventListener("click", onClick));
  return { state };
}
