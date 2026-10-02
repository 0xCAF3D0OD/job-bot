/// <reference types="vitest/config" />
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// Le frontend appelle l'API en chemin relatif (/api/...). En développement, Vite
// relaie ces appels vers le backend ; en production, c'est le reverse proxy ou l'Ingress.
const apiTarget = process.env.JOBBOT_DEV_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
  },
});
