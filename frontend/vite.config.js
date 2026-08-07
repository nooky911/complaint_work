import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  optimizeDeps: {
    esbuildOptions: {
      concurrency: 1,
    },
  },
  server: {
    watch: {
      ignored: [
        "**/__pycache__/**",
        "**/*.log",
        "**/logs/**",
        "**/venv/**",
        "**/.venv/**",
      ],
    },
  },
});
