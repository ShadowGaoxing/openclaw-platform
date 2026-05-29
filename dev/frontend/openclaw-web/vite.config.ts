import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws/nats': {
        target: 'ws://localhost:9222',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
