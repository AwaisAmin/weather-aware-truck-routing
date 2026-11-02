import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // In development, /api is proxied to the Django server so no CORS setup is needed.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    // MapLibre alone is ~1.1 MB (300 KB gzip); it is lazy-loaded, so only warn above that.
    chunkSizeWarningLimit: 1200,
    rolldownOptions: {
      output: {
        // Long-lived vendor chunks cache across deploys; MapLibre stays in the lazy map chunk.
        codeSplitting: {
          groups: [
            { name: 'react', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
            { name: 'mui', test: /node_modules[\\/](@mui[\\/](material|system|utils|styled-engine)|@emotion)[\\/]/ },
            { name: 'date-pickers', test: /node_modules[\\/](@mui[\\/]x-date-pickers|dayjs)[\\/]/ },
          ],
        },
      },
    },
  },
})
