import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API calls to FastAPI backend during development
    // so we avoid CORS issues in dev
    proxy: {
      '/auth': 'http://localhost:8000',
      '/profile': 'http://localhost:8000',
      '/learning-maps': 'http://localhost:8000',
      '/topics': 'http://localhost:8000',
      '/progress': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
