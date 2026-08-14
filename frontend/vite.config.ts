import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Pinned, and deliberately NOT 5173: the AUX reference app runs there.
    // Without this, Vite silently auto-increments when the port is taken and
    // you end up unsure which app you are looking at.
    port: 5174,
    strictPort: true,
    proxy: { "/api": "http://localhost:8000" },
  },
});
