// En premier : son écouteur du bouton retour doit passer avant celui du routeur (backListeners.ts).
import "./backListeners";

import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { useTextSize } from "./composables/useTextSize";
import { useTheme } from "./composables/useTheme";
import "@fontsource-variable/figtree";
import "./style.css";

// Après une mise à jour, une page restée ouverte demande des fichiers de l'ancienne version, qui
// n'existent plus : on recharge la page une fois pour prendre la nouvelle, au lieu d'une page
// blanche (audit du 22.10.2026). Une seule fois par minute, pour ne jamais boucler.
const RELOADED = "jobA1-reloaded-at";
function reloadOnce(): void {
  try {
    const last = Number(sessionStorage.getItem(RELOADED) ?? 0);
    if (Date.now() - last < 60_000) return;
    sessionStorage.setItem(RELOADED, String(Date.now()));
  } catch {
    // Stockage indisponible : on recharge quand même, une fois par page.
  }
  window.location.reload();
}
window.addEventListener("vite:preloadError", (event) => {
  event.preventDefault();
  reloadOnce();
});
router.onError((error: unknown) => {
  if (/dynamically imported module|Importing a module script failed|error loading dynamically/i.test(String(error))) reloadOnce();
});

// Barres de défilement classiques (Windows, Linux, Mac avec souris) : leur place reste réservée (html.scrollbars-classic,
// style.css), pour que la page ne glisse pas de côté quand une page courte s'affiche (Kevin, 15.11.2026).
const probe = document.createElement("div");
probe.style.cssText = "position:absolute;top:-99px;width:50px;height:50px;overflow:scroll";
document.body.append(probe);
document.documentElement.classList.toggle("scrollbars-classic", probe.offsetWidth > probe.clientWidth);
probe.remove();

// L'apparence choisie (Clair, Sombre) avant le premier rendu : pas d'éclair de l'autre thème.
useTheme().apply();
useTextSize().apply();
createApp(App).use(router).mount("#app");
