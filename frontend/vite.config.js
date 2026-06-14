import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy /api and /ws to the FastAPI backend during local development so the
// frontend can use same-origin relative URLs (no CORS headaches). Override the
// backend target with VITE_BACKEND_URL if it runs somewhere other than :8000.
const backend = process.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/ws': { target: backend.replace(/^http/, 'ws'), ws: true, changeOrigin: true },
    },
  },
})
