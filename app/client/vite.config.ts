import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})