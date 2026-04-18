import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/classify-all": "http://localhost:8000",
      "/model-stats": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/stream": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
