/// <reference types="vitest/config" />
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// Le frontend appelle l'API en chemin relatif (/api/...). En développement, Vite
// relaie ces appels vers le backend ; en production, c'est le reverse proxy ou l'Ingress.
const apiTarget = process.env.JOBBOT_DEV_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  // L'« Options API » de Vue (data(), methods, computed: dans un export default {}) coupée au build : aucun composant
  // de l'app ni des bibliothèques chargées ne s'en sert, tous sont écrits avec setup (vérifié le 16.11, PR « Vue sans
  // Options API »). Gain : 1,65 Ko de JS gzip (Kevin, 16.11 : alléger avant de dépasser). Un composant écrit à
  // l'ancienne ne s'afficherait plus : écrire les composants en <script setup>. Les tests (vitest) n'en dépendent pas.
  define: { __VUE_OPTIONS_API__: "false" },
  // Le manifeste dit quels fichiers chaque page charge : le budget de poids le lit (docs/117 §3).
  build: {
    manifest: true,
    rolldownOptions: {
      output: {
        // Un seul fichier pour ce que toute page charge avec l'application (#664) : Vue, vue-router, openapi-fetch,
        // et nos modules que l'entrée importe toujours (client de l'API, icônes, dates, langue, logo). Séparés, ils
        // faisaient autant de fichiers compressés chacun à part et une ligne d'import longue dans chaque page.
        // Le budget (scripts/poids.mjs) compte tous les fichiers : regrouper ce qui se charge ensemble l'allège,
        // découper l'alourdirait. Rien ne change dans ce que chaque page télécharge.
        codeSplitting: {
          includeDependenciesRecursively: false,
          groups: [
            {
              name: "commun",
              test: /node_modules[\\/].*\.m?js$|src[\\/](api[\\/]client\.ts|icons\.ts|dates\.ts|lang\.ts|brandPaths\.ts|components[\\/]AppIcon\.vue)/,
            },
            // Pas de groupe « partage » (retiré le 16.11 après #795) : réunir les petits composants partagés allégeait
            // js-total de 2,7 Ko, mais chaque page qui en chargeait un les recevait tous (Trier, Alertes, Relances,
            // Résultats, Formations et État du service : de + 5,6 à + 12,9 Ko). Les limites portent sur les pages.
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
    // Deux processus : sous charge, davantage de processus ne démarraient pas tous à temps.
    maxWorkers: 2,
    // Un fichier de test qui ne démarre pas fait échouer la suite (vitest.total.ts).
    reporters: ["default", "./vitest.total.ts"],
  },
});
