import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
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

createApp(App).use(router).mount("#app");
