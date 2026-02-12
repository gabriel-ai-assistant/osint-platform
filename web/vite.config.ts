import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/osint/',
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/osint/api': {
        target: 'http://localhost:8450',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8450',
        changeOrigin: true,
      },
    },
  },
})
