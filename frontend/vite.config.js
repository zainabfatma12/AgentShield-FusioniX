import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { nodePolyfills } from "vite-plugin-node-polyfills";

export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      include: ["buffer", "process", "stream", "crypto", "util"]
    })
  ],
  define: {
    global: "globalThis"
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/health": { target: "http://127.0.0.1:8000" },
      "/providers": { target: "http://127.0.0.1:8000" },
      "/payment": { target: "http://127.0.0.1:8000" },
      "/analyze": { target: "http://127.0.0.1:8000" },
      "/authorize": { target: "http://127.0.0.1:8000" },
      "/transactions": { target: "http://127.0.0.1:8000" },
      "/trust": { target: "http://127.0.0.1:8000" }
    }
  }
});
