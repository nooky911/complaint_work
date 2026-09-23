import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  optimizeDeps: {
    holdDependenciesInMemory: false,
    esbuildOptions: {
      sourcemap: false,
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://fastapi_app:8000',
        changeOrigin: true,
      },
    },
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
