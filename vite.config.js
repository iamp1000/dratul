import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  root: 'admin_app',
  plugins: [react()],
  build: {
    outDir: '../dist'
  },
  server: {
    port: 5173,
    open: true
  }
})
