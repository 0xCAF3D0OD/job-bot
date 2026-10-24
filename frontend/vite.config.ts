/// <reference types="vitest/config" />
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// Le frontend appelle l'API en chemin relatif (/api/...). En développement, Vite
// relaie ces appels vers le backend ; en production, c'est le reverse proxy ou l'Ingress.
const apiTarget = process.env.JOBBOT_DEV_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  // Le manifeste dit quels fichiers chaque page charge : le budget de poids le lit (docs/117 §3).
  build: { manifest: true },
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
