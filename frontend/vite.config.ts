import {defineConfig, loadEnv} from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backend = env.VITE_BACKEND_PROXY_TARGET || "http://localhost:8001";

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": {target: backend, changeOrigin: true},
        "/demo-assets": {target: backend, changeOrigin: true},
      },
    },
  };
});
